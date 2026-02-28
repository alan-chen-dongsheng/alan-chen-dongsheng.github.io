# Copilot Instructions

## 项目概述

这是一个基于 [tailwind-nextjs-starter-blog](https://github.com/timlrx/tailwind-nextjs-starter-blog) 的个人技术博客，使用 Next.js 15 (App Router) + Tailwind CSS v4 + TypeScript + contentlayer2 构建，部署在 Vercel 上。博客主要语言为中文（zh-CN）。

## 常用命令

```bash
yarn dev          # 启动开发服务器
yarn build        # 生产构建（同时运行 postbuild.mjs 生成搜索索引）
yarn lint         # ESLint 自动修复（覆盖 pages/app/components/lib/layouts/scripts）
yarn analyze      # 分析 bundle 大小
```

> 无测试套件。

## 架构概览

### 内容层（contentlayer2）

- 所有内容源文件位于 `data/` 目录
- **博客文章**：`data/blog/**/*.mdx` → 类型为 `Blog`
- **作者简介**：`data/authors/**/*.mdx` → 类型为 `Authors`
- contentlayer2 在构建/dev 时自动将 MDX 编译为类型安全的 JSON，输出到 `.contentlayer/`
- `onSuccess` 钩子会：
  1. 生成 `app/tag-data.json`（tag 计数）
  2. 生成 `public/search.json`（kbar 本地搜索索引，若配置了 kbar）

### Next.js App Router

- `app/` 为路由根目录，使用 App Router
- `layouts/` 目录存放文章渲染布局（`PostLayout`、`PostBanner`、`PostSimple`、`ListLayout`、`ListLayoutWithTags`、`AuthorLayout`）
- `components/` 存放共享 UI 组件，`MDXComponents.tsx` 注册 MDX 自定义组件

### 站点配置

- `data/siteMetadata.js` — 全局站点元数据、analytics、评论、搜索提供商配置
- `data/headerNavLinks.ts` — 导航栏链接
- `data/projectsData.ts` — Projects 页面数据
- `next.config.js` — 用 `withContentlayer` 和 `withBundleAnalyzer` 包裹，配置了 CSP headers

## 博客文章 Frontmatter 格式

```yaml
---
title: 文章标题
date: '2024-12-04'
tags:
  - tag1
  - tag2
draft: false          # true 则在生产环境中隐藏
summary: '摘要文字'
images: []            # 可选，用于 og:image
authors:              # 可选，默认使用 data/authors/default.mdx
  - default
layout: PostLayout    # 可选：PostLayout | PostBanner | PostSimple
bibliography: references-data.bib  # 可选，引用文件
canonicalUrl: ''      # 可选
---
```

- 文件名建议使用英文或拼音，避免路径问题（支持中文文件名但需注意 URL 编码）
- `slug` 由 contentlayer 从文件路径自动计算（去除 `blog/` 前缀）

## MDX 支持的增强语法

- **数学公式**：KaTeX（行内 `$...$`，块级 `$$...$$`）
- **代码块标题**：`` ```js:文件名.js ``
- **GitHub 风格警告块**：`> [!NOTE]`、`> [!WARNING]` 等
- **引用**：通过 `rehype-citation`，引用文件放 `data/` 目录下
- **图片优化**：`remarkImgToJsx` 自动将 `img` 转为 Next.js `<Image>`

## 代码风格

- Prettier：无分号、单引号、100 字符宽度、`es5` trailing comma，插件 `prettier-plugin-tailwindcss`
- ESLint：TypeScript + jsx-a11y + Next.js + prettier
- 提交前 husky + lint-staged 自动格式化

## 新增作者

在 `data/authors/` 下创建 `.mdx` 文件，frontmatter 包含 `name`、`avatar`、`occupation`、`company`、`email`、`github` 等字段，`layout` 字段指定布局（默认 `AuthorLayout`）。
