---
title: MLIR学习笔记
date: '2025-12-31'
tags:
    - mlir
    - "AI infra"
draft: false
summary: "学习MLIR的笔记"
---

# MLIR学习

[YouTube MLIR beginner 教程](http://youtube.com/watch?v=Uno_XhtkT5E)

## 一、获取模型



- 下载onnx模型

[onnx model zoo ](https://github.com/onnx/models/tree/main)



将模型从动态shape切换为固定shape

```python3
# /home/cds/model_repo/mobilenetv2-12.onnx
import onnx
from onnx import shape_inference
# Load the ONNX model
model = onnx.load("/home/cds/model_repo/mobilenetv2-12.onnx")
# 加载完模型是，这是一个N维度动态shape的onnx模型
# 请将N设置为1， 然后导出一个静态图
model.graph.input[0].type.tensor_type.shape.dim[0].dim_value = 1
# Perform shape inference
model = shape_inference.infer_shapes(model)
# 打印模型的计算图
print(onnx.helper.printable_graph(model.graph))
onnx.save(model, "/home/cds/model_repo/mobilenetv2-12-batch1.onnx")
```



执行推理



```shell
#!/bin/bash

model_path="/home/cds/model_repo/mobilenetv2-12-batch1.onnx"
front_ir_name="mobilenetv2-12-batch1.mlir"
execute_name="mobilenetv2-12-batch1.vmfb"


iree-import-onnx ${model_path} \
  --opset-version 17 \
  -o=${front_ir_name}


iree-compile \
  ${front_ir_name}\
  --iree-hal-target-device=local \
  --iree-hal-local-target-device-backends=llvm-cpu \
  --iree-llvmcpu-target-cpu=host \
  -o ${execute_name}

# 可以查看执行的函数名为什么
iree-dump-module ./mobilenetv2-12-batch1.vmfb

iree-run-module \
  --module=${execute_name} \
  --device=local-task \
  --function=torch-jit-export \
  --input="1x3x224x224xf32=2"
```



## 二、调试



```shell
主要的日志相关参数：

-mlir-print-ir-before-all - 在每个 pass 执行前打印 IR
-mlir-print-ir-after-all - 在每个 pass 执行后打印 IR
-mlir-print-ir-module-scope - 以完整模块范围打印 IR
-mlir-timing - 显示每个 pass 的执行时间
-mlir-print-op-on-diagnostic=true - 诊断时打印操作信息
-mlir-elide-elementsattrs-if-larger=N - 控制大型常量属性的打印

额外的调试选项：

--iree-llvmcpu-debug-symbols=true - 生成调试符号
--iree-vm-bytecode-module-output-format=flatbuffer-text - 输出可读的字节码格式
IREE_LLVM_EMBEDDED_LINKER_TOOL_VERBOSE=1 - 环境变量，增加链接器详细程度
```



## 三、MLIR需要补充的知识



在`IREEImportPublicPass` 里， 使用了 `patternRewrite`   相关的技术， 继承了  `OpConversionPattern` ，需要学习一下，这个是如何转换的。



`ConversionPattern`













# IREE的学习计划

MLIR的四个核心目标：

1.  **RewritePattern / OpRewritePattern**

2. **DialectConversion（ConversionTarget + TypeConverter）**
3. Pass 注入与 pipeline 定位
4. IR 可视化与 Debug（print-ir-after / dump）













# MLIR



## PassInstrumentation

**PassInstrumentation 是一种“钩子（Hooks）”机制**，它允许你在 Pass 执行的各个生命周期注入自定义代码，而无需修改 Pass 自身的逻辑。



### 1. 它是用来干什么的？

在编译器的内部，`PassManager` 负责调度成百上千个 Pass。如果你想观察这个过程，不能去给每个 Pass 都写打印语句。`PassInstrumentation` 提供了一个**非侵入式**的观测点，主要用于实现以下功能：

- **打印 IR (`-mlir-print-ir-after-all`)**：在每个 Pass 运行前后对比 IR 的变化。
- **性能计时 (`-mlir-print-pass-timing`)**：统计每个 Pass 消耗了多少毫秒，找出编译性能瓶颈。
- **可视化/跟踪 (`-mlir-print-pass-pipeline-crash`)**：如果编译器崩了，它能告诉你死在了哪个 Pass。
- **正确性验证**：在每个 Pass 之后运行 `Verify` 检查 IR 是否合法。

### 2. 核心工作原理

`PassInstrumentation` 实际上是一个基类，定义了一系列虚函数（回调点）。当你向 `PassManager` 注册一个 Instrumentation 实例后，`PassManager` 在执行流水线时会自动调用这些方法：

| **钩子函数 (Virtual Methods)** | **触发时机**                        |
| ------------------------------ | ----------------------------------- |
| `runBeforePass`                | Pass 执行逻辑开始前                 |
| `runAfterPass`                 | Pass 执行逻辑完成后（无论成功失败） |
| `runBeforeAnalysis`            | 分析（Analysis）运行前              |
| `runAfterAnalysis`             | 分析运行后                          |
| `runAfterPipeline`             | 整个 Op 管道（Pipeline）执行结束时  |







# 一、MLIR的内部调试工具

## 1.1 reduce- 筛出最小复现问题的IR

在现实中你经常会遇到这种情况：

- 一个模型 lowering 出来是 **几万行 MLIR**
- 跑 `mlir-opt` / `mlir-translate` / 后端 codegen **直接崩溃 / assert / 生成错误代码**
- 你**根本没法手动删 IR**，因为：
  - 删一个 op，bug 消失
  - 改一个 attr，问题又不复现

 **`mlir-reduce` 就是来自动“删 IR” 的**。



它做的事和 `creduce`、`llvm-reduce` 本质一样：

1. **你告诉它：**
   - “什么样算 bug 还在？”
2. **它不断尝试：**
   - 删除 op
   - 删除 block / region
   - 删除 function / module
   - 简化 attribute / type
3. **每一步都运行你的判定条件**
4. **只保留“删了还能触发 bug”的最小子集**

最后你得到的不是“完整模型 IR”，而是：

> 一个 **几十行 / 几行** 的 MLIR，却**100% 复现问题**



1️⃣ 准备一个“触发 bug 的 MLIR 文件”

比如：

```
bad.mlir
```

你确认下面这个命令会失败 / 崩溃 / 触发 assert：

```
mlir-opt bad.mlir --your-pass
```

------

2️⃣ 写一个“判定脚本”（最关键）

`mlir-reduce` 不知道什么是 bug，它只知道：

> **你告诉我：运行这个脚本返回 0，说明 bug 还在**

示例 `test.sh`：

```
#!/bin/bash
mlir-opt "$1" --your-pass > /dev/null 2>&1
# 如果 mlir-opt 崩溃，返回非 0 → bug 还在
```

或者你想判断 **输出错误**：

```
#!/bin/bash
mlir-opt "$1" --your-pass | grep "WRONG_CODE"
```

记得：

```
chmod +x test.sh
```

------

3️⃣ 运行 mlir-reduce

```
mlir-reduce bad.mlir -test=test.sh
```

然后它会开始疯狂尝试：

```
Trying to reduce functions...
Trying to reduce operations...
Trying to reduce attributes...
...
```

最后输出：

```
reduced.mlir
```

## 1.2 action

[action](https://mlir.llvm.org/docs/ActionTracing/)

在 MLIR 生态中，有很多“事情”可以对 IR 做：

- 跑一组 pass
- 验证 IR 是否合法
- 打印 / 导出 IR
- 对 IR 做一次变换再检查结果
- 判断“某个 bug 是否还存在”

这些事情**不只是 pass 本身**，而是：

- pass + 前后处理
- 失败/成功的判定
- 是否需要回滚 IR

👉 **Action 就是把这些事情包装成一个“可调度的动作”**。

「当你需要“反复、试探性地对 IR 做修改，并根据结果决定是否保留这些修改”时，缺乏统一、可回滚、可判定的执行模型」这个问题。

Action 解决的是：如何系统化地做“对 IR 的实验”。

**核心思想：把“试探性修改”建模成一等公民**

Action 把下面这件事标准化了：

1. 备份当前 IR
2. 尝试做一次修改（删 / 改 / 简化）
3. 执行一个判定（test / checker）
4. 根据结果：
   - 保留修改
   - 或回滚







# 二、MLIR的内部开发工具

## ODS

[Operation Definition Specification ](https://mlir.llvm.org/docs/DefiningDialects/Operations/)

- TableGen `class` 类似于 C++ 类；它可以进行模板化和子类化。
- TableGen `def` 类似于 C++ 对象；它可以通过特化 TableGen `class` 来声明（例如， `def MyDef : MyClass<...>;` ），也可以完全独立声明（例如， `def MyDef;` ）。它不能被进一步模板化或子类化。
- TableGen `dag` 是一种专门用于表示元素有向无环图的类型。 `dag` 包含一个运算符和零个或多个参数。其语法为 `(operator arg0, arg1, argN)` 。运算符可以是任何 TableGen `def` ；参数可以是任何内容，包括 `dag` 本身。运算符和参数都可以附加名称，例如 `(MyOp:$op_name MyArg:$arg_name)` 。



## 2.1 定义方言

[MLIR文档-Defining Dialect](https://mlir.llvm.org/docs/DefiningDialects/)



完全可以参考： `third_party/llvm-project/mlir/include/mlir/IR/DialectBase.td` 的定义



```c++
def IREEEncoding_Dialect : Dialect {
  let name = "iree_encoding";
  let cppNamespace = "::mlir::iree_compiler::IREE::Encoding";
  let summary = [{
    A dialect designed for tensor encoding attributes and ops.
  }];
  let description = [{des}];
  let extraClassDeclaration = [{
    void registerAttributes();
  }];
  let useDefaultAttributePrinterParser = 1;
}

```



把 `def` 名字里的 `_Dialect` 后缀去掉，再加上 `Dialect` 作为类名惯例：

- `IREEEncoding_Dialect`
  - 去掉 `_Dialect` → `IREEEncoding`
  - 加 `Dialect` → **`IREEEncodingDialect`**



生成的效果：

```c++
class IREEEncodingDialect : public ::mlir::Dialect {
  explicit IREEEncodingDialect(::mlir::MLIRContext *context);

  void initialize();
  friend class ::mlir::MLIRContext;
public:
  ~IREEEncodingDialect() override;
  static constexpr ::llvm::StringLiteral getDialectNamespace() {
    return ::llvm::StringLiteral("iree_encoding");
  }

  /// Parse an attribute registered to this dialect.
  ::mlir::Attribute parseAttribute(::mlir::DialectAsmParser &parser,
                                   ::mlir::Type type) const override;

  /// Print an attribute registered to this dialect.
  void printAttribute(::mlir::Attribute attr,
                      ::mlir::DialectAsmPrinter &os) const override;

    void registerAttributes();
  };

} // namespace mlir::iree_compiler::IREE::Encoding
```







## 2.2 定义type



- 属性和类型

  - 属性： 不可变的常量数据机制，有些地方不准许使用变量
  - 类型： 类似编程语言的数据类型

  定义属性和类型的语法在MLIR里基本类似， cmake做tablegen的时候，有些差异。

  建议将属性类和类型类定义在不同的 `.td` 文件中，以便更好地封装它们。





[mlir-文档-type](https://mlir.llvm.org/docs/DefiningDialects/AttributesAndTypes/)





参考： `third_party/llvm-project/mlir/include/mlir/IR/AttrTypeBase.td`

```c++
// type
class MyDialect_Type<string name, string typeMnemonic, list<Trait> traits = []>
    : TypeDef<My_Dialect, name, traits> {
  let mnemonic = typeMnemonic;
}

// attribute
class MyDialect_Attr<string name, string attrMnemonic, list<Trait> traits = []>
    : AttrDef<My_Dialect, name, traits> {
  let mnemonic = attrMnemonic;
}
```









## 2.3 定义op

`third_party/llvm-project/mlir/include/mlir/IR/OpBase.td`



```c++
def IREEEncoding_SetEncodingOp : IREEEncoding_PureOp<"set_encoding",[
   DeclareOpInterfaceMethods<ReifyRankedShapedTypeOpInterface, ["reifyResultShapes"]>, Pure
  ]>
```



这个OP的定义 `IREEEncoding_SetEncodingOp`

TableGen 生成 C++ wrapper 类时，会把 `def` 名字里的 `Op` 后缀去掉，并把前缀（通常是 Dialect/文件前缀）去掉，只保留“核心 op 名”，因此得到：

- `IREEEncoding_SetEncodingOp`
  - 去掉 dialect 前缀 `IREEEncoding_`
  - 去掉尾巴 `Op`
  - 剩下 `SetEncoding`
- 然后加上 `Op` 作为类名惯例 → **`SetEncodingOp`**

所以我之前说的 `SetEncodingOp` 是按 MLIR/IREE 这类项目里最常见的生成结果（“去前缀 + 去 Op 再加 Op”这种风格）。



生成结果：

```c++
class SetEncodingOp : public ::mlir::Op<SetEncodingOp, ::mlir::OpTrait::ZeroRegions, ::mlir::OpTrait::OneResult, ::mlir::OpTrait::OneTypedResult<::mlir::RankedTensorType>::Impl, ::mlir::OpTrait::ZeroSuccessors, ::mlir::OpTrait::OneOperand, ::mlir::OpTrait::OpInvariants, ::mlir::ReifyRankedShapedTypeOpInterface::Trait, ::mlir::ConditionallySpeculatable::Trait, ::mlir::OpTrait::AlwaysSpeculatableImplTrait, ::mlir::MemoryEffectOpInterface::Trait>
```






## 2.4interface 接口

参考： [MLIR文档-Interface](https://mlir.llvm.org/docs/Interfaces/)



MLIR 提供了三种层面的接口：

| **类型**               | **作用对象**         | **典型例子**                                                 |
| ---------------------- | -------------------- | ------------------------------------------------------------ |
| **OpInterface**        | 具体的 **Operation** | `TilingInterface` (用于 Linalg 瓦片化), `InferTypeOpInterface` (推导返回类型) |
| **TypeInterface**      | **数据类型** (Type)  | `MemRefElementTypeInterface` (判断是否能作为 MemRef 的元素)  |
| **AttributeInterface** | **属性** (Attribute) | 比较通用的属性描述                                           |



我只关心这个op有没有实现某个能力，如果实现了我就可以过滤出来。

而不用关心这个OP现在是什么方言，我不用对不同类型的方言，写不同的实现。

```c++
if (auto iface = dyn_cast<SomeOpInterface>(op)) {
  iface.doSomething();
}
```

可以实现Pass **与 Dialect 解耦** 新 Dialect 只要实现 Interface，Pass 自动生效





`third_party/llvm-project/mlir/include/mlir/IR/Interfaces.td`






## Conversion

[MLIR文档-Dialect Conversion](https://mlir.llvm.org/docs/DialectConversion/#)

1. 主要用于方言间的降低

   1. > 它的设计初衷和主要威力在「方言之间」

2. 次要用于方言内部的结构调整



| **特性**     | **Transformation (Rewrite/Canonicalize)** | **Conversion**                        |
| ------------ | ----------------------------------------- | ------------------------------------- |
| **主要目标** | 优化、简化（如 $x * 1 \to x$）            | 改变抽象层级（Lowering）              |
| **类型改变** | 通常不改变数据类型                        | **支持并处理类型转换**                |
| **完整性**   | 部分转换，不保证消除所有特定 Op           | 目标导向，必须将特定方言转换干净      |
| **API**      | `RewritePattern`                          | `ConversionPattern` + `TypeConverter` |











## MLIR 转 LLVM

| 机制           | 本质                         |
| -------------- | ---------------------------- |
| RewritePattern | **局部等价替换**             |
| Canonicalize   | **规范形态收敛**             |
| Conversion     | **语义阶段迁移（Lowering）** |



[LLVM IR Target](https://mlir.llvm.org/docs/TargetLLVMIR/)



## Pass的基础设置

[Pass Infrastructure](https://mlir.llvm.org/docs/PassManagement/#)





## transformation  Pattern rewriting



[transformation](https://mlir.llvm.org/docs/PatternRewriter/#)



# 三、IR设计的开发工具



## 3.1 Bufferization

> **MLIR 的 Bufferization 是用来解决：
>  「如何把 \*以值（tensor）为中心、隐含内存语义\* 的 IR，系统地转换成 \*以显式内存（buffer/memref）为中心、可分析可分配\* 的 IR」这个问题。**

换句话说：

> **Bufferization 解决的是：从“数学/函数式视角的张量计算”，过渡到“硬件可执行的内存读写模型”。**

高层 IR 的世界

- tensor 是不可变值
- op = 纯函数
- 内存是隐含的
- alias 默认不存在

硬件/低层 IR 的世界

- memref 指向真实内存
- 读/写是显式的
- alias 必须受控
- 生命周期必须清楚

👉 **Bufferization 就是连接这两个世界的桥梁。**

```shell
High-level tensor IR
   (mhlo / linalg / tensor)
        ↓
  Bufferization   ← 关键分水岭
        ↓
Low-level memory IR
   (memref / scf / affine)
        ↓
  Liveness / Allocation / Scheduling
        ↓
 Codegen

```



关于内存有：

out-of-place：分配新 buffer, 重新来一次读写

in-place：直接覆盖  相当于forwarding，乒乓流水

- 关于使用

❌ 错误用法

bufferize 之后直接继续 lowering
 👉 allocator bug、overlap、peak 不可控

------

✅ 正确用法

bufferize 后 **立刻做三件事之一（或全部）**：

1. **Liveness 分析**
2. **Static SRAM allocation**
3. **Alias 验证 / 断言**

> **Bufferization 不是终点，是“内存分析的起点”。**



- 关于什么时候需要Bufferization

> **在“算法结构基本确定，但内存必须开始算”的那一刻。**

具体信号是：

- 你要开始做：
  - SRAM 静态分配
  - buffer timeline
  - in-place 决策
- 你需要：
  - 明确每一块 buffer 的生命周期
  - 知道哪些 tensor alias

# 技巧



- 如何遍历IR
  - https://mlir.llvm.org/docs/Tutorials/UnderstandingTheIRStructure/
- mlir-opt
  - `mlir-opt` 工具可以将文本形式的 IR 或字节码加载到内存结构中，并可选择执行一系列操作，然后再将 IR（默认为文本形式）序列化回原始数据。它是一款测试和调试工具。
  - 不带任何参数运行 `mlir-opt` 会从标准输入读取文本或字节码形式的 IR，对其进行解析并运行验证器，然后将文本格式写回标准输出。这是测试输入的 MLIR 是否格式良好的好方法。
  - 作用
    - 单独调用一个pass
    -





# 词汇表

- CSE (Common Subexpression Elimination) —— 公共子表达式消除

- DCE (Dead Code Elimination) —— 死代码消除
