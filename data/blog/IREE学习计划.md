---
title: IREE compielr Leaning object
date: '2026-01-25'
tags:
    - IREE
    - "AI infra"
draft: false
summary: "Iree compiler 学习目标"
---
# IREE compielr学习目标

# 关于目标



**目标：**

找到一个卷积算子， onnx格式的， 从IREE编译到我司的ASM，并成功在我司NPU上运行。



```mathematica
阶段 1（现在）
Input MLIR
  ↓
IREE 编译管线
  ↓
Flow / Dispatch
  ↓
【你的 Compiler Backend】
  ↓
NPU IR / Binary / Task Graph
  ↓
【你的 Runtime】

阶段 2（迁移）
Flow / Dispatch
  ↓
IREE Stream
  ↓
HAL Executable
  ↓
IREE HAL Driver
  ↓
NPU

```







| 层级                   | 适合度 | 说明                  |
| ---------------------- | ------ | --------------------- |
| Linalg on Tensors      | ⭐⭐     | 太偏算子图，调度缺失  |
| Linalg on Buffers      | ⭐⭐⭐    | 有 buffer，但仍偏通用 |
| **IREE Flow Dispatch** | ⭐⭐⭐⭐   | **强烈推荐**          |
| IREE Stream            | ⭐⭐⭐    | 已偏 runtime 调度     |
| HAL Executable         | ⭐      | 已绑定 runtime        |



- 关于将mlir转为支持我司架构的npu asm结构。

1. 从 `Flow` 后劫持IR生成，
2. 第一阶段就导出json就行了。
3. 第二阶段在引入DIalect
   1. 用于表达：
      - 指令级算子
      - tile / cluster / memory scope
      - 硬件专有属性



在IREE里新增一个 `target`  `pass pipeline` `pass` ，不要在IREE已有的pass里去改代码。



- 关于MLIR

熟悉一下四个即可。

**RewritePattern / OpRewritePattern**

**DialectConversion（ConversionTarget + TypeConverter）**

**Pass 注入与 pipeline 定位**

**IR 可视化与 Debug（print-ir-after / dump）**





# 学习计划

### 第 1 周：把 IREE 编译 pipeline 拆清楚（只看 compiler）

**目标**：你知道“从输入 MLIR 到 Flow/Dispatch 中间，每一步是谁干的”

**任务**

- 用 `iree-compile` + `--print-ir-after-all`
- 对一个极小模型（1 个 matmul）
- 标注：
  - 哪个 pass 产生了 dispatch
  - dispatch 里剩下哪些 op（linalg / arith / memref）

**交付**

- 一张 pipeline 手绘/文档图
- 明确你“要插 pass 的位置”













------

### 第 2 周：在 Flow Dispatch 层写你的第一个 pass

**目标**：你能“截获 dispatch”，并遍历其中的 op

**任务**

- 写一个 pass：
  - 遍历 `flow.dispatch.region`
  - 收集算子类型、shape、dtype
  - 打印或导出为文本

**交付**

- 一个 pass，可以输出：

  ```
  Dispatch #3:
    op: linalg.matmul
    M=128 N=128 K=64
    dtype: f16
  ```

------

### 第 3 周：把 Dispatch 转成“你的 NPU 可执行表示（草稿版）”

**目标**：你开始“像写后端一样思考”

**任务**

- 定义 **你的 NPU 中间表示（先不用 MLIR）**：
  - JSON / protobuf / C++ struct
- 在 pass 里：
  - 每个 dispatch → 一个 NPU task
  - 记录 buffer 依赖、输入输出

**交付**

- 一个 `model.npu.json`
- 你已有 runtime 能加载并“假执行 / 仿真”

------

### 第 4 周：做合法性 & 子图切分（决定什么能跑 NPU）

**目标**：你能决定“哪些 dispatch 能下沉到 NPU”

**任务**

- 制定规则：
  - 支持哪些 op
  - 支持哪些 dtype / shape
- 不支持的 dispatch：
  - 标记为 fallback
  - 或直接拒绝（先简单）

**交付**

- 编译期能明确提示：

  ```
  Dispatch #7 not supported: dynamic shape
  ```

------

### 第 5–6 周：引入 NPU Dialect（可选，但强烈建议）

**目标**：让你的 IR 不再是“字符串导出”

**任务**

- 定义最小 `npu` dialect：
  - `npu.matmul`
  - `npu.conv`
- 从 Flow Dispatch → NPU Dialect

**交付**

- MLIR 文件里出现：

  ```
  npu.matmul %A, %B -> %C {tile_m=64, tile_n=64}
  ```

------

### 第 7 周：调度 / tiling / memory 决策前移到编译期

**目标**：你开始吃掉 runtime 的工作

**任务**

- 在 lowering pass 中：
  - 插入 tiling 参数
  - 标注 SRAM / DRAM
- 这些信息最终会被你 runtime 使用

**交付**

- NPU IR 明确包含：
  - tile
  - memory space
  - execution order

------

### 第 8 周：为未来切换 IREE runtime 留好接口

**目标**：你不返工

**任务**

- 确保你的 NPU IR：
  - 可以自然映射为：
    - HAL executable
    - 或 IREE 的 command buffer 模型
- 不把 runtime 假设写死在 compiler

**交付**

- 一份设计文档：
  - “从当前 NPU IR → IREE HAL executable 的映射方案”



# 插件系统

插件系统最初的设计讨论： https://github.com/iree-org/iree/issues/12520

IREE官方推荐的一个插件： https://github.com/nod-ai/iree-amd-aie/blob/main/iree_compiler_plugin.cmake





# 第一周: 编译路程熟悉



## 1. onnx模型MLIR

onnx 模型,刚从onnx转位MLIR的, 这个时候还是 `torch` 方言.

```shell
module {
  func.func @SingleConv(%arg0: !torch.vtensor<[1,3,500,500],f32>) -> !torch.vtensor<[1,8,498,498],f32> attributes {torch.onnx_meta.ir_version = 10 : si64, torch.onnx_meta.opset_version = 22 : si64, torch.onnx_meta.producer_name = "single_conv_example", torch.onnx_meta.producer_version = ""} {
    %0 = torch.operator "onnx.Constant"() {torch.onnx.value = dense_resource<weight> : tensor<8x3x3x3xf32>} : () -> !torch.vtensor<[8,3,3,3],f32> 
    %1 = torch.operator "onnx.Constant"() {torch.onnx.value = dense_resource<bias> : tensor<8xf32>} : () -> !torch.vtensor<[8],f32> 
    %none = torch.constant.none
    %2 = torch.operator "onnx.Conv"(%arg0, %0, %1) {torch.onnx.pads = [0 : si64, 0 : si64, 0 : si64, 0 : si64], torch.onnx.strides = [1 : si64, 1 : si64]} : (!torch.vtensor<[1,3,500,500],f32>, !torch.vtensor<[8,3,3,3],f32>, !torch.vtensor<[8],f32>) -> !torch.vtensor<[1,8,498,498],f32> 
    return %2 : !torch.vtensor<[1,8,498,498],f32>
  }
}

{-#
  dialect_resources: {
    builtin: {
      weight: "0x08000000A6CE943D1788E53FD7A10140154D2D3FC47E323DC55AA4BFDB2645BF4F2183BF37CD40C0646ACE3E06D4993FC71E84BF257D17C0C7536BBF3E001ABFFD3E80BF2FD5A5BFD5B737BF6C83C23F230083BD374F463F5BC152BEF05CC03FB61496BFA3643F3FDF68AB3F6710403FA614423F523CC53DA7DEC8BEA124F83E7590123E30650E407FAD913C89937FBE876C83BEF643F6BE7A05A9BFEAD9D9BFD6DBA03EB54A9BBE7FF2B5BE80645F3EA13D75BE7F7A94BFDBCDFB3ED7381DBE2A60243E512C173E8264F9BE450EE23FD2ABD03E27C3D63F72C985BF633EC73E195C86BF37732ABE25918EBF3E42EEBFEC3E283F953B733EDF88423FAEFA21BEEF26713FBE27AA3E1D2503BFCE554DBF44C576BF7457AA3E12D1663FF8F50540EFF18EBF5C9A243CEE6DBEBF260C4BBE4D58E5BE4BA1D2BF1FFF0ABF9D658EBE6A2F853FE9E007BF3849A2BF74C1BFBFDFDFBABFE72C073FA31385BFB917433EF94DEE3F1E06F93EA631ED3E4864B23F23107D3F7A0BE53DA733813E240B21BF12F906BFC57ED73E3C91CA3DDA50D9BEE4EE14C01D616B3EDC4C12BFA690823E31D60840DA9A333FC65D753D3DCB93BF6BC993BF344A033F12B5033EE9B14DBD026E68BF4100E03E507623405B18DA3ECDCB8CBE14B7C8BE27E2024084DC683F6980AFBE213E13404A55D5BFB287AEBFC5CDC83E9A169D3E64B13E3E51FD26BF53F98EBF456A2DBF9E92833F06B780BEB6FCAEBF65F4863F5FF82E3FE488AF3F76EAEC3E404DC33CF6176D400617FABDBA42073FED6BD7BEA695B9BEF7FA9B3EE58C3EBE3237D93F9F4C05405292983F30EB8A3FE7DB99BE18987DBD2D4BCFBE1CA6893CFAFA9B3DC3410BBFED62AA3FA034AD3ED2B0A23FC0E88BBF355E203E662A463F8C7FA33F0B093DBF4F639BBF668CE53FFA51EF3C35FDB53EAD64D5BA14408DBFA545703F5135563D70C1203F33536EBF960BC53F62166A3F76CA17BF6F30AFBEA0FCB1BF3120B8BEC5CBAE3EC8105A3F0ED14CBF75083C3F31BFB3BEBC0D5DBFEBD83E3F0350923D1934853EF95C3540918923BFA5D54BBF9D5E76BE64FC373FF534CA3E7ED2AF3FDD82463FE6AB933FC3ED463FD917E63FC56C16BFD620B93FD4999F3FDBF5E0BFA70F8DBEE981913E99CA2FBF8DEB863E0C0D9DBD8EEFB23EF6441E3F357F33BF33B8983F5D24F0BE0A0880BFE6C1013F4B0B2FBFB06C1ABF",
      bias: "0x08000000D180A73D310345BF6E86D83EC1FD4ABE25D8B3BDA28C5BBF5781BC3F028715BD"
    }
  }
#-}


```

## 2. 进入编译管线

### 2.1 input

我们可以看到input 这个阶段, 就已经转位 `arith` 和  `linalg` 方言里



**目的**：将高层模型（如 TensorFlow、ONNX）转化为 IREE 编译器能够理解的中间表示（MLIR）。

- **问题**：来自不同框架的模型表示方式各不相同，必须统一成一个可以处理的格式。
- **解决方案**：IREE 通过使用如 `mhlo` 或 `stablehlo` 方言来引入来自 TensorFlow 或 JAX 的模型，然后将这些表示转化为 MLIR 格式。

```shell
module {
  util.func public @SingleConv$async(%arg0: !hal.buffer_view, %arg1: !hal.fence, %arg2: !hal.fence) -> !hal.buffer_view attributes {inlining_policy = #util.inline.never, iree.abi.model = "coarse-fences", iree.abi.stub} {
    %cst = arith.constant dense<"0xA6CE943D1788E53FD7A10140154D2D3FC47E323DC55AA4BFDB2645BF4F2183BF37CD40C0646ACE3E06D4993FC71E84BF257D17C0C7536BBF3E001ABFFD3E80BF2FD5A5BFD5B737BF6C83C23F230083BD374F463F5BC152BEF05CC03FB61496BFA3643F3FDF68AB3F6710403FA614423F523CC53DA7DEC8BEA124F83E7590123E30650E407FAD913C89937FBE876C83BEF643F6BE7A05A9BFEAD9D9BFD6DBA03EB54A9BBE7FF2B5BE80645F3EA13D75BE7F7A94BFDBCDFB3ED7381DBE2A60243E512C173E8264F9BE450EE23FD2ABD03E27C3D63F72C985BF633EC73E195C86BF37732ABE25918EBF3E42EEBFEC3E283F953B733EDF88423FAEFA21BEEF26713FBE27AA3E1D2503BFCE554DBF44C576BF7457AA3E12D1663FF8F50540EFF18EBF5C9A243CEE6DBEBF260C4BBE4D58E5BE4BA1D2BF1FFF0ABF9D658EBE6A2F853FE9E007BF3849A2BF74C1BFBFDFDFBABFE72C073FA31385BFB917433EF94DEE3F1E06F93EA631ED3E4864B23F23107D3F7A0BE53DA733813E240B21BF12F906BFC57ED73E3C91CA3DDA50D9BEE4EE14C01D616B3EDC4C12BFA690823E31D60840DA9A333FC65D753D3DCB93BF6BC993BF344A033F12B5033EE9B14DBD026E68BF4100E03E507623405B18DA3ECDCB8CBE14B7C8BE27E2024084DC683F6980AFBE213E13404A55D5BFB287AEBFC5CDC83E9A169D3E64B13E3E51FD26BF53F98EBF456A2DBF9E92833F06B780BEB6FCAEBF65F4863F5FF82E3FE488AF3F76EAEC3E404DC33CF6176D400617FABDBA42073FED6BD7BEA695B9BEF7FA9B3EE58C3EBE3237D93F9F4C05405292983F30EB8A3FE7DB99BE18987DBD2D4BCFBE1CA6893CFAFA9B3DC3410BBFED62AA3FA034AD3ED2B0A23FC0E88BBF355E203E662A463F8C7FA33F0B093DBF4F639BBF668CE53FFA51EF3C35FDB53EAD64D5BA14408DBFA545703F5135563D70C1203F33536EBF960BC53F62166A3F76CA17BF6F30AFBEA0FCB1BF3120B8BEC5CBAE3EC8105A3F0ED14CBF75083C3F31BFB3BEBC0D5DBFEBD83E3F0350923D1934853EF95C3540918923BFA5D54BBF9D5E76BE64FC373FF534CA3E7ED2AF3FDD82463FE6AB933FC3ED463FD917E63FC56C16BFD620B93FD4999F3FDBF5E0BFA70F8DBEE981913E99CA2FBF8DEB863E0C0D9DBD8EEFB23EF6441E3F357F33BF33B8983F5D24F0BE0A0880BFE6C1013F4B0B2FBFB06C1ABF"> : tensor<8x3x3x3xf32>
    %cst_0 = arith.constant dense<[0.0817886665, -0.769579946, 0.422900617, -0.198233619, -0.0878146067, -0.857614636, 1.47269714, -0.0365057066]> : tensor<8xf32>
    %0 = hal.tensor.import wait(%arg1) => %arg0 : !hal.buffer_view -> tensor<1x3x500x500xf32>
    %1 = tensor.empty() : tensor<1x8x498x498xf32>
    %broadcasted = linalg.broadcast ins(%cst_0 : tensor<8xf32>) outs(%1 : tensor<1x8x498x498xf32>) dimensions = [0, 2, 3] 
    %2 = linalg.conv_2d_nchw_fchw {dilations = dense<1> : vector<2xi64>, strides = dense<1> : vector<2xi64>} ins(%0, %cst : tensor<1x3x500x500xf32>, tensor<8x3x3x3xf32>) outs(%broadcasted : tensor<1x8x498x498xf32>) -> tensor<1x8x498x498xf32>
    %3 = hal.tensor.barrier join(%2 : tensor<1x8x498x498xf32>) => %arg2 : !hal.fence
    %4 = hal.tensor.export %3 : tensor<1x8x498x498xf32> -> !hal.buffer_view
    util.return %4 : !hal.buffer_view
  }
  util.func public @SingleConv(%arg0: !hal.buffer_view) -> !hal.buffer_view attributes {iree.abi.stub} {
    %0 = util.null : !hal.fence
    %c-1_i32 = arith.constant -1 : i32
    %c0 = arith.constant 0 : index
    %device_0 = hal.devices.get %c0 : !hal.device
    %fence = hal.fence.create device(%device_0 : !hal.device) flags("None") : !hal.fence
    %1 = util.call @SingleConv$async(%arg0, %0, %fence) : (!hal.buffer_view, !hal.fence, !hal.fence) -> !hal.buffer_view
    %status = hal.fence.await until([%fence]) timeout_millis(%c-1_i32) flags("None") : i32
    util.return %1 : !hal.buffer_view
  }
}

```



## 2.2 abi

**目的**：将输入的数据转化为符合应用程序二进制接口（ABI）的格式，确保它们适应不同硬件平台。

- **问题**：输入数据并不直接适配 IREE 的运行时环境，需要做适配转换，特别是为了满足硬件的内存布局和访问需求。
- **解决方案**：在 ABI 预处理阶段，模型会被转化为一种适应目标平台的格式，涉及张量数据布局转化、内存对齐和硬件特定的优化。



这一步单独的卷积,在CPU上,这一步IR没有变化.

### 2.3 preprocessing



在IR的基础上,增加了以下的信息,

IREE 编译器在 **preprocessing 阶段** 生成的与目标平台相关的配置信息。具体来说，它定义了 **目标硬件**（例如 x86_64 架构）以及该硬件的特性、数据布局和一些特定的编译设置。以下是每个部分的详细解释：

```shell
#executable_target_embedded_elf_x86_64 = #hal.executable.target<"llvm-cpu", "embedded-elf-x86_64", {cpu = "skylake", cpu_features = "+64bit,+adx,+aes,-amx-avx512,-amx-bf16,-amx-complex,-amx-fp16,-amx-fp8,-amx-int8,-amx-movrs,-amx-tf32,-amx-tile,+avx,-avx10.1,-avx10.2,+avx2,-avx512bf16,-avx512bitalg,-avx512bw,-avx512cd,-avx512dq,-avx512f,-avx512fp16,-avx512ifma,-avx512vbmi,-avx512vbmi2,-avx512vl,-avx512vnni,-avx512vp2intersect,-avx512vpopcntdq,-avxifma,-avxneconvert,-avxvnni,-avxvnniint16,-avxvnniint8,+bmi,+bmi2,-ccmp,-cf,-cldemote,+clflushopt,-clwb,-clzero,+cmov,-cmpccxadd,+crc32,+cx16,+cx8,-egpr,-enqcmd,+f16c,+fma,-fma4,+fsgsbase,+fxsr,-gfni,-hreset,+invpcid,-kl,-lwp,+lzcnt,+mmx,+movbe,-movdir64b,-movdiri,-movrs,-mwaitx,-ndd,-nf,+pclmul,-pconfig,-pku,+popcnt,-ppx,-prefetchi,+prfchw,-ptwrite,-push2pop2,-raoint,-rdpid,-rdpru,+rdrnd,+rdseed,-rtm,+sahf,-serialize,+sgx,-sha,-sha512,-shstk,-sm3,-sm4,+sse,+sse2,+sse3,+sse4.1,+sse4.2,-sse4a,+ssse3,-tbm,-tsxldtrk,-uintr,-usermsr,-vaes,-vpclmulqdq,-waitpkg,-wbnoinvd,-widekl,-xop,+xsave,+xsavec,+xsaveopt,+xsaves,-zu", data_layout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128", iree.encoding.resolver = #iree_cpu.cpu_encoding_resolver<>, max_stack_allocation_size = 32768 : i64, native_vector_size = 32 : i64, target_triple = "x86_64-unknown-unknown-eabi-elf"}>
```

这段 IR 描述的是 IREE 编译器在 **preprocessing 阶段** 生成的与目标平台相关的配置信息。具体来说，它定义了 **目标硬件**（例如 x86_64 架构）以及该硬件的特性、数据布局和一些特定的编译设置。以下是每个部分的详细解释：

------

#### **1. `hal.executable.target<...>` 解析**

这一部分是 **IREE 编译器生成的目标平台信息**，它用于指定代码将要生成并执行在哪个硬件平台上。具体来说，这段 IR 中：

- **目标平台**：`"llvm-cpu", "embedded-elf-x86_64"`，表示目标是 **x86_64 架构的嵌入式系统**，并且是通过 **LLVM** 编译器生成的 ELF 可执行文件。
- **硬件特性**：`cpu = "skylake"` 指定目标处理器为 **Skylake**，这是英特尔的一款处理器架构。

------

#### **2. `cpu_features` 字段**

这个字段列出了目标 CPU 支持的各种指令集和功能特性。比如：

- **`+64bit`**：支持 64 位架构。
- **`+avx`**：启用 AVX（高级向量扩展）指令集。
- **`-avx512`**：禁用 AVX-512 指令集。
- 还有许多其他的指令集特性，这些特性会影响编译时生成的代码以利用特定硬件功能，提升性能。

这些 CPU 特性为 IREE 提供了一个明确的硬件执行上下文，确保在该平台上生成的代码能够正确地利用硬件的能力。

------

#### **3. `data_layout` 字段**

`data_layout` 定义了目标平台的数据布局，它指定了内存中数据的排列方式：

- **`e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128`**：这是 x86_64 平台特定的数据布局，涉及整数、浮点数、字节对齐等方面的细节。这个布局信息会影响到如何对数据进行存储和访问，优化内存访问模式。

------

#### **4. `iree.encoding.resolver`**

这一部分是与 IREE 的 CPU 编码解析器相关的配置。它定义了 IREE 编译器如何解析和处理 CPU 相关的编码信息，从而生成能够在目标硬件上运行的代码。

------

#### **5. `max_stack_allocation_size`**

**`max_stack_allocation_size = 32768 : i64`** 指定了 **最大栈分配大小**，也就是说，栈上最多可以分配 32KB 的内存空间。

这个参数在嵌入式系统或有严格内存限制的设备上尤为重要。

------

#### **6. `native_vector_size`**

**`native_vector_size = 32 : i64`** 定义了该硬件平台的 **本地向量化大小**，即每次可以并行处理的元素数量。此信息帮助编译器在生成代码时最大化硬件利用率，利用硬件的 SIMD（单指令多数据）指令集进行并行计算。

------

#### **7. `target_triple`**

**`target_triple = "x86_64-unknown-unknown-eabi-elf"`** 定义了目标系统的三元组（target triple），它告诉编译器生成哪种类型的代码。

- **`x86_64`**：目标平台是 64 位 x86 架构。
- **`unknown-unknown`**：表示操作系统和 ABI（应用二进制接口）是未知的，这通常用于嵌入式系统。
- **`eabi-elf`**：指定了生成的是 **嵌入式应用程序二进制接口（EABI）格式** 的 ELF 文件。

------

#### **总结：**

这段 IR 描述的是在 **IREE 编译器的 preprocessing 阶段**，生成了与目标平台（如 x86_64、Skylake 处理器）相关的详细配置信息。它主要为后续的编译阶段提供了硬件特性、数据布局、指令集支持等信息，从而确保生成的代码能够在指定的硬件上高效执行。

- **硬件特性**：明确目标平台的 CPU 和支持的指令集。
- **数据布局**：定义内存中数据的组织方式，优化访问。
- **编译器配置**：如栈分配大小、向量大小、目标三元组等，为编译器生成优化的代码。

这些信息都是为了确保 IREE 能够生成适配特定硬件的代码，以提高性能并确保兼容性。





### 2.4 global-optimization



### 2.5 flow



### 2.6 stream



### 2.7 executable-sources



### 2.8 executable-targets



### 2.9 hsl



### 2.10 vm





在异构计算框架（如 IREE、TensorFlow 的 XLA 或类似编译器后端）中，**Fence（栅栏）** 是一种用于同步主机与设备、或设备与设备之间执行顺序的机制。
