#!/usr/bin/env python3
"""
同步 IREE docs 目录下的 markdown 文件到博客目录
- 转换为 .mdx 格式
- 添加符合博客格式的 frontmatter
- 自动生成摘要和标签
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# 配置
SOURCE_DIR = "/Users/alanchen/workspace/iree/alan_iree/docs"
TARGET_DIR = "/Users/alanchen/github/alan-chen-dongsheng.github.io/data/blog"
DEFAULT_TAGS = ["IREE", "编译器", "MLIR"]
DRAFT_MODE = False  # 默认设为 false，设为 true 表示草稿


def extract_title_and_content(file_path: Path) -> Tuple[str, str]:
    """从 markdown 文件中提取标题和内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 尝试提取第一个标题 (# 或 ## 开头)
    lines = content.split("\n")
    title = file_path.stem  # 默认用文件名作为标题

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            # 移除标题行，避免重复
            content = "\n".join(lines[i + 1 :])
            break
        elif line.startswith("## "):
            title = line[3:].strip()
            # 不移除二级标题，只作为文件名
            break

    # 清理标题中的特殊字符
    title = title.strip().strip('"').strip("'")
    return title, content


def generate_summary(content: str, max_length: int = 150) -> str:
    """从内容中生成摘要"""
    # 移除代码块
    content = re.sub(r"```[\s\S]*?```", "", content)
    # 移除标题
    content = re.sub(r"^#.*$", "", content, flags=re.MULTILINE)
    # 移除空行和空白
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    # 移除表格
    lines = [line for line in lines if not line.startswith("|")]

    text = " ".join(lines)

    # 截取前 max_length 个字符
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "..."

    return text


def extract_tags(content: str, file_name: str) -> list:
    """从内容和文件名中提取标签"""
    tags = DEFAULT_TAGS.copy()

    # 关键词映射
    keyword_map = {
        "onnx": "ONNX",
        "pass": "Pass",
        "dialect": "Dialect",
        "编译": "编译原理",
        "前端": "编译器前端",
        "后端": "编译器后端",
        "debug": "调试",
        "优化": "编译优化",
        "llvm": "LLVM",
        "cpu": "CPU",
        "gpu": "GPU",
        "cuda": "CUDA",
        "vulkan": "Vulkan",
        "性能": "性能优化",
    }

    content_lower = content.lower()
    file_lower = file_name.lower()

    for keyword, tag in keyword_map.items():
        if keyword in content_lower or keyword in file_lower:
            if tag not in tags:
                tags.append(tag)

    return tags


def get_file_date(file_path: Path) -> str:
    """获取文件的修改日期"""
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def build_frontmatter(
    title: str,
    date: str,
    tags: list,
    summary: str,
    draft: bool = DRAFT_MODE,
    authors: list = ["default"],
) -> str:
    """构建博客 frontmatter"""
    # 处理 title 中的特殊字符
    if ":" in title or "'" in title:
        title_line = f'title: "{title}"'
    else:
        title_line = f"title: '{title}'"

    tags_str = "\n".join([f"  - {tag}" for tag in tags])
    authors_str = "\n".join([f"  - {author}" for author in authors])

    frontmatter = f"""---
{title_line}
date: '{date}'
tags:
{tags_str}
draft: {str(draft).lower()}
summary: '{summary}'
---

"""
    return frontmatter


def convert_md_to_mdx(file_path: Path) -> str:
    """将 markdown 内容转换为 mdx 兼容格式"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 移除第一个标题（如果存在，会被 frontmatter 替代）
    content = re.sub(r"^# .*$\n?", "", content, count=1, flags=re.MULTILINE)

    # 2. 处理特殊的 MDX 字符（< > 等可能需要转义，但在代码块中不需要）
    # 这里暂时不做处理，因为大部分内容是安全的

    return content


def sync_file(md_file: Path, target_dir: Path) -> bool:
    """同步单个 markdown 文件到博客目录"""
    # 提取信息
    title, _ = extract_title_and_content(md_file)
    content = convert_md_to_mdx(md_file)
    summary = generate_summary(content)
    tags = extract_tags(content, md_file.name)
    date = get_file_date(md_file)

    # 构建 frontmatter
    frontmatter = build_frontmatter(title, date, tags, summary)

    # 目标文件名（.md -> .mdx）
    target_file = target_dir / (md_file.stem + ".mdx")

    # 写入文件
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(frontmatter)
        f.write(content)

    print(f"✓ {md_file.name} -> {target_file.name}")
    print(f"  标题: {title}")
    print(f"  标签: {', '.join(tags)}")
    print(f"  摘要: {summary[:50]}...")
    print()
    return True


def sync_directory(source_dir: Path, target_dir: Path, recursive: bool = True):
    """同步整个目录下的 markdown 文件"""
    if recursive:
        md_files = list(source_dir.rglob("*.md"))
    else:
        md_files = list(source_dir.glob("*.md"))

    # 跳过 README.md
    md_files = [f for f in md_files if f.name.lower() != "readme.md"]

    print(f"找到 {len(md_files)} 个 markdown 文件\n")

    success_count = 0
    for md_file in sorted(md_files):
        try:
            sync_file(md_file, target_dir)
            success_count += 1
        except Exception as e:
            print(f"✗ 处理失败 {md_file.name}: {e}")
            import traceback

            traceback.print_exc()
            print()

    print(f"\n完成！成功同步 {success_count}/{len(md_files)} 个文件")


def main():
    source_path = Path(SOURCE_DIR)
    target_path = Path(TARGET_DIR)

    if not source_path.exists():
        print(f"错误: 源目录不存在: {source_path}")
        return 1

    if not target_path.exists():
        print(f"错误: 目标目录不存在: {target_path}")
        return 1

    print(f"源目录: {source_path}")
    print(f"目标目录: {target_path}")
    print(f"默认标签: {DEFAULT_TAGS}")
    print(f"Draft 模式: {DRAFT_MODE}")
    print("-" * 60)
    print()

    sync_directory(source_path, target_path, recursive=True)

    return 0


if __name__ == "__main__":
    exit(main())
