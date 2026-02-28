---
title: 学习ONNX计算图的定义
date: '2025-12-15'
tags: ['ai compiler']
draft: false
summary: '学习ONNX计算图的定义'
---


# 学习ONNX计算图的定义

```protobuf
message GraphProto {
  // node
  repeated NodeProto node = 1;

  // 图的名字
  optional string name = 2;   // namespace Graph

  // tensor具体的存储，数据类型，名字，维度
  repeated TensorProto initializer = 5;

  // 文本表示的图，用于展示图的内容
  optional string doc_string = 10;

  // 整张图的输入，输出，还有中间的tensor
  repeated ValueInfoProto input = 11;
  repeated ValueInfoProto output = 12;
  repeated ValueInfoProto value_info = 13;

}
```

## 输入，输出，中间tensor

整个模型的输入，输出，和中间的tensor， 都是只存储了一个 tensor name。

```protobuf
message ValueInfoProto {
  // This field MUST be present in this version of the IR.
  optional string name = 1;     // namespace Value
  // This field MUST be present in this version of the IR for
  // inputs and outputs of the top-level graph.
  optional TypeProto type = 2;
  // A human-readable documentation for this value. Markdown is allowed.
  optional string doc_string = 3;
  // Named metadata values; keys should be distinct.
  repeated StringStringEntryProto metadata_props = 4;
}
```

## tensor

```protobuf
message TensorProto {
  enum DataType {
    UNDEFINED = 0;
    FLOAT = 1;   // float
    UINT8 = 2;   // uint8_t
    INT8 = 3;    // int8_t
    UINT16 = 4;  // uint16_t
    INT16 = 5;   // int16_t
    INT32 = 6;   // int32_t
    INT64 = 7;   // int64_t
    STRING = 8;  // string
    BOOL = 9;    // bool
  }

  // The shape of the tensor.
  repeated int64 dims = 1;

  // The data type of the tensor.
  // This field MUST have a valid TensorProto.DataType value
  optional int32 data_type = 2;


  // Optionally, a name for the tensor.
  optional string name = 8; // namespace Value

  // A human-readable documentation for this tensor. Markdown is allowed.
  optional string doc_string = 12;

  enum DataLocation {
    DEFAULT = 0;
    EXTERNAL = 1;
  }

}
```

## node

```protobuf
message NodeProto {
  // 输入和输出的tensor的名字
  repeated string input = 1;    // namespace Value
  repeated string output = 2;   // namespace Value

  // node的名字
  optional string name = 3;     // namespace Node

  // node的属性
  repeated AttributeProto attribute = 5;

  // 文本展示node
  optional string doc_string = 6;
}
```
