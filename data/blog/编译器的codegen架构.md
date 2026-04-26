---
title: '编译器的 codegen 架构'
date: '2026-04-26'
tags:
  - 编译器
  - CodeGen
draft: false
summary: '编译器 codegen 架构的几种方案对比及工程实践注意事项。'
---

# 编译器的codegen架构

## 架构方案

1. 每个 OP 都 codegen，手写，适合快速原型
2. 使用 YAML，生成每一种 64-bit 的格式，自动生成 `encoder`、`decoder`、`checker`
   1. 用 YAML/JSON/TOML 描述每种 64-bit 格式
   2. 自动生成 C++ encoder/decoder/checker
   3. 编译器内部操作语义对象，不直接碰 uint64_t
3. 自定义 DSL 或 TableGen 风格描述格式

## 工程实现需要注意

无论你选哪条路，最好都支持：

### 1. encode

语义对象 → 64bit

### 2. decode

64bit → 可读字段

### 3. verify

检查：

- 字段是否越界
- 是否冲突
- 是否满足特定 OP 约束

### 4. pretty print

比如：

```
0x8C12000000000002
op_type = CONV
device  = NPU
stride  = 1
kernel  = 3
pad     = 1
```

这个对调试特别重要。
