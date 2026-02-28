---
title: huggingFace基础知识
date: '2026-1-19'
tags: ['LLM']
draft: false
summary: "huggingFace基础知识"
---



# 基础知识

# huggingFace

- hugging face的三个作用

![alt text](image.png)

## 一、模型的大小



本次示例模型 huggingFace 地址： [Qwen-0.5B](https://huggingface.co/Qwen/Qwen2.5-0.5B/tree/main)

GitHub的地址是： [Qwen-0.5B](https://github.com/QwenLM/Qwen3?tab=readme-ov-file)

可以看到GitHub的文档： [GitHub   Qwen文档](https://qwen.readthedocs.io/zh-cn/latest/training/llama_factory.html)

![image-20260118171551207](C:\Users\alanchen\AppData\Roaming\Typora\typora-user-images\image-20260118171551207.png)





模型的 0.3B 指的是它的参数量约为 3 亿（0.3 × 10⁹）。
B 是 Billion（十亿）的缩写，所以 0.3B = 300,000,000 个参数。
参数是模型在训练过程中学习到的 “知识” 载体，数量的多少直接影响模型的能力和运行需求。

## 二、查看显卡显存

我是有8G的显存，

```shell
(torch_gpu) ➜  huggingFace nvidia-smi
Sat Jan 17 15:48:43 2026
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.86.09              Driver Version: 571.96         CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4060        On  |   00000000:01:00.0  On |                  N/A |
|  0%   53C    P5             N/A /  115W |    2457MiB /   8188MiB |      4%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A              24      G   /Xwayland                             N/A      |
+-----------------------------------------------------------------------------------------+
```

## 三、显存-参数量 对应关系

- 显存占用 (推理) ≈ 模型参数量 (B) × 4 ~ 模型参数量 (B) × 8
  - ×4 倍 → 模型用 FP32（32位浮点） 存储，最基础格式，所有模型默认加载方式，显存占用最大；
  - ×2 倍 → 模型用 FP16（16位半精度） 存储，你的 RTX4060 完美支持，也是我们 8G 显存的「最优格式」，显存直接减半，速度还能提升 30%，无任何精度损失；
  - ×8 倍 → 推理 / 加载时的「峰值显存」，包含了：模型参数 + 输入数据缓存 + 输出缓存，是显卡一瞬间的最大占用，实际稳定占用就是 ×4 或 ×2；

✅ 显存占用 (推理，FP16 半精度) ≈ 模型参数量 (B) × 2
✅ 显存占用 (微调，FP16 半精度) ≈ 模型参数量 (B) × 3 ~ 4

## 四、调用hugging face的模型到本地执行

### 4.1 模型下载

#### 4.1.1下载到本地（支持微调）

下载模型有这个模型名字就可以了， 下面这2种方式都支持断点续传的

![image-20260117163744571](C:\Users\alanchen\AppData\Roaming\Typora\typora-user-images\image-20260117163744571.png)

- 使用hugging face的命令行

```shell

huggingface-cli download Qwen/Qwen2.5-0.5B --local-dir ./qwen2.5-0.5b-local --local-dir-use-symlinks False
```

`--local-dir`：指定本地保存路径，你可以改成任何想放的位置

`--local-dir-use-symlinks False`：避免符号链接问题，直接下载完整文件



- 使用python

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen2.5-0.5B",
    local_dir="./qwen2.5-0.5b-local",
    local_dir_use_symlinks=False
)
```



#### 4.1.2 快速执行模式（不适合修改模型)

下面代码会自动下载模型， 存储到：

- Linux/macOS：`~/.cache/huggingface/hub`
- Windows：`C:\Users\你的用户名\.cache\huggingface\hub`

**通过这种代码下载的方式，不适合需要备份 / 修改模型文件**

> - 这种方式本质是为了快速复用而设计的缓存，不是为了让你拿到完整的模型文件去备份或修改，具体有几个关键问题：
> - 文件存储分散且隐藏
> - 模型会被拆分成多个碎片文件，存放在 ~/.cache/huggingface/hub 里的哈希命名目录中，比如 models--Qwen--Qwen2.5-0.5B。
> - 这些目录名是自动生成的哈希值，你很难直接找到和管理，更别说完整备份了。
> - 缓存目录里还会混合其他模型的文件，时间久了会变得非常混乱。
> - 文件格式不可直接修改
> - 缓存里的权重文件（如 .safetensors）是被「锁定」的，如果你手动修改了缓存里的文件，下次加载模型时，transformers 会检测到文件哈希值不匹配，认为文件损坏，然后重新下载覆盖你的修改。
> 这意味着你对缓存文件的任何修改都是无效的，无法永久保存。

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-0.5B"

# 加载分词器和模型
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",  # 自动分配到GPU/CPU
    torch_dtype="auto"  # 自动用FP16半精度，省显存
)

# 测试生成
prompt = "帮我写一个PyTorch微调文本回归模型的代码片段"
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(
    **inputs,
    max_new_tokens=512,  # 生成的最大长度
    temperature=0.7,     # 生成的随机性
    do_sample=True
)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)

```

### 4.2 查看模型结构



#### 4.2.1 可视化查看模型结构

在 [huggingface的model_structure_viewer](https://huggingface.co/spaces/maomao88/model_structure_viewer) 这里输入模型的名字， 就可以在线看到这些大语言模型的结构。



![image-20260117203434204](C:\Users\alanchen\AppData\Roaming\Typora\typora-user-images\image-20260117203434204.png)



#### 4.2.2 文本查看模型结构

通过python 代码来查看模型结构。

```python
# 所有的模型都下载到本地目录：
# /home/cds/model_repo/qwen2.5-0.5b-local


from transformers import AutoTokenizer, AutoModelForCausalLM

# 指向你刚才下载的本地路径
local_model_path = "/home/cds/model_repo/qwen2.5-0.5b-local"

# 加载分词器和模型
tokenizer = AutoTokenizer.from_pretrained(local_model_path)
model = AutoModelForCausalLM.from_pretrained(
    local_model_path,
    device_map="auto",
    torch_dtype="auto",
    trust_remote_code=True,  # Qwen 模型需要这个参数
)

# 1. 打印模型的完整结构（文本形式）
print("===== 模型结构 =====")
print(model)

# 2. 统计模型参数量（快速了解规模）
total_params = sum(p.numel() for p in model.parameters())
print(f"\n===== 模型参数量 =====")
print(f"总参数量: {total_params / 1e9:.2f} B")  # 0.5B 左右，和页面标注一致

# 3. 查看模型的层级结构（更清晰）
print("\n===== 模型层级 =====")
for name, module in model.named_modules():
    if hasattr(module, "weight") and "embed" not in name:
        print(f"层: {name}, 参数数量: {module.weight.numel()}")

import torch

torch.save(model.state_dict(), "./qwen2.5-0.5b_model.pth")  # 导出权重+结构
torch.save(model, "./qwen2.5-0.5b_full_model.pth")  # 导出完整模型（推荐这个）

```





## 五、大模型微调



|     框架      |        核心亮点        |       适用人群       |
| :-----------: | :--------------------: | :------------------: |
| LLaMA-Factory | 全功能、Web UI、零门槛 |     新手、全场景     |
|    Unsloth    |   极致速度、显存优化   | 个人开发者、追求性能 |
|    Axolotl    |    配置驱动、轻量级    |  开发者、自动化训练  |
|      TRL      | 高级对齐技术、科研友好 | 科研人员、进阶开发者 |
|   MS-SWIFT    |    企业级、云端集成    | 企业用户、大规模训练 |



GitHub的地址是： [Qwen-0.5B](https://github.com/QwenLM/Qwen3?tab=readme-ov-file)

可以看到GitHub的文档，提供了微调方案： [GitHub   Qwen文档](https://qwen.readthedocs.io/zh-cn/latest/training/llama_factory.html)

![image-20260118171551207](C:\Users\alanchen\AppData\Roaming\Typora\typora-user-images\image-20260118171551207.png)
