# Alan Chen's Blog

> 个人技术博客，主要记录 AI Compiler、MLIR/IREE、前端工程、软件开发等方向的学习笔记与思考。

🌐 **线上地址**：[https://alanchen.vercel.app](https://alanchen.vercel.app) | [https://alan-chen-dongsheng.github.io](https://alan-chen-dongsheng.github.io)
📦 **源码仓库**：[github.com/alan-chen-dongsheng/alan-chen-dongsheng.github.io](https://github.com/alan-chen-dongsheng/alan-chen-dongsheng.github.io)

---

## 关于本博客

这个博客由 **alanchen** 编写，内容涉及：

- 🤖 AI Compiler（MLIR、IREE、TVM、ONNX）
- 🧠 大语言模型推理与 AI Infra
- 💻 前端工程与 Next.js
- 🛠️ 软件工程工具与开发实践

文章由本人撰写，但日常维护、Bug 修复、代码重构等"脏活"由 **GitHub Copilot** 协助完成。AI 是这个博客不可缺少的合作者之一。

---

## 基于的开源项目

本博客基于 [timlrx/tailwind-nextjs-starter-blog](https://github.com/timlrx/tailwind-nextjs-starter-blog) fork 而来。

原项目是目前功能最完整的 Next.js + Tailwind CSS 博客模板之一，具备：

- **Next.js 15 App Router** + React Server Components
- **contentlayer2** 驱动的 MDX/MD 内容管理，自动生成类型定义
- **Tailwind CSS v4** 样式系统
- KaTeX 数学公式、代码高亮、引用文献、GitHub Alert 等 MDX 增强
- 内置 Analytics（Umami/Plausible/GA）、评论（Giscus/Utterances）、全文搜索（kbar/Algolia）
- SEO 友好：RSS、Sitemap、结构化数据
- 亮色/暗色主题切换

感谢 [timlrx](https://www.timlrx.com) 及所有贡献者构建了如此优秀的基础模板。

---

## 本仓库的定制内容

在上游模板基础上，本仓库做了以下调整：

- **支持 `.md` 文件**：除 `.mdx` 外，`data/blog/` 下的普通 Markdown 文件也会被收录展示
- **修复 headlessui v2 SSR Hydration 错误**：移除 `MobileNav` 中 `unmount={false}` 解决 SSR/客户端 DOM 不匹配问题
- **GitHub Copilot Skill**：`.github/skills/sync-upstream/` 提供一键同步上游更新的 Copilot skill
- **Copilot 项目说明**：`.github/copilot-instructions.md` 记录了架构、约定和常用命令，帮助 AI 助手快速理解项目

---

## 快速开始

```bash
# 安装依赖
yarn

# 启动开发服务器
yarn dev

# 生产构建
yarn build
```

访问 [http://localhost:3000](http://localhost:3000) 查看本地效果。

---

## 写博客

在 `data/blog/` 目录下创建 `.mdx` 或 `.md` 文件，添加必要的 frontmatter：

```yaml
---
title: '文章标题'
date: '2025-01-01'
tags:
  - tag1
draft: false
summary: '文章摘要'
---
```

保存后开发服务器会自动热更新。

---

## 同步上游更新

```bash
# 使用 Copilot CLI（推荐）
# 在 Copilot CLI 中输入：Use the /sync-upstream skill
```

或者手动执行：

```bash
git fetch upstream
git merge upstream/main --no-edit
# 冲突处理：package.json 用 upstream，yarn.lock / data/** 保留本地
```

---

## License

博客内容（`data/blog/`）版权归 alanchen 所有。

框架代码遵循原项目协议：[MIT](https://github.com/timlrx/tailwind-nextjs-starter-blog/blob/main/LICENSE) © [Timothy Lin](https://www.timlrx.com)

