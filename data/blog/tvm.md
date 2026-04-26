---
title: TVM的笔记
date: '2026-04-26'
tags:
    - TVM
    - "AI infra"
draft: false
summary: 'TVM 编译器的学习总结笔记。'
---

# 学习TVM的笔记





## 编译TVM



```shell
# 直接在项目根目录下,执行下面的命令就开始安装了.
pip install -e .      
```





## debug TVM





# TVM执行流程



将以onnx 为例, 尝试看下TVM的编译流程.

## 1. 前端IR导入



[官网文档: 模型导入](https://tvm.apache.org/docs/how_to/tutorials/import_model.html)



## 2. 编译



```python

mod = from_exported_program(exported_program, keep_params_as_input=True)
mod, params = relax.frontend.detach_params(mod)
TOTAL_TRIALS = 512  # Change to 20000 for better performance if needed
MAX_TRIALS_PER_TASK = 16  # Change to more trials per task for better performance if needed
target = tvm.target.Target("nvidia/geforce-rtx-3090-ti")  # Change to your target device
work_dir = "tuning_logs"


# 跑Pass的环节
if not IS_IN_CI:
    mod = relax.get_pipeline(
        "static_shape_tuning",
        target=target,
        work_dir=work_dir,
        total_trials=TOTAL_TRIALS,
        max_trials_per_task=MAX_TRIALS_PER_TASK,
    )(mod)

    # Only show the main function
    mod["main"].show()
    
    
# 部署的环节
with target:
    mod = tvm.s_tir.transform.DefaultGPUSchedule()(mod)
    ex = tvm.compile(mod, target=target)
    dev = tvm.device("cuda", 0)
    vm = relax.VirtualMachine(ex, dev)
    # Need to allocate data and params on GPU device
    gpu_data = tvm.runtime.tensor(np.random.rand(1, 3, 224, 224).astype("float32"), dev)
    gpu_params = [tvm.runtime.tensor(p, dev) for p in params["main"]]
    gpu_out = vm["main"](gpu_data, *gpu_params)[0].numpy()

    print(gpu_out.shape)
```

## 3. 新建pass, 组织pipeline

[文档](https://tvm.apache.org/docs/how_to/tutorials/customize_opt.html)





# 设计和架构

onnx -> relax -> tensor IR

## relax

图优化和转换的高级抽象层





## Tensor IR 
