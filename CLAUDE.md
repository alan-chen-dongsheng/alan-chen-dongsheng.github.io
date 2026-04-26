# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal tech blog built on Next.js 15 (App Router) + Tailwind CSS v4 + TypeScript + contentlayer2. Deployed on Vercel. Primary language is Chinese (zh-CN). Forked from [timlrx/tailwind-nextjs-starter-blog](https://github.com/timlrx/tailwind-nextjs-starter-blog).

## Common Commands

```bash
yarn              # Install dependencies
yarn dev          # Start dev server (http://localhost:3000)
yarn build        # Production build (runs postbuild.mjs for search index)
yarn serve        # Start production server locally
yarn analyze      # Bundle size analysis
yarn lint         # ESLint auto-fix
```

No test suite exists.

## Architecture

### Content Layer (contentlayer2)

- All content source files live in `data/`
- **Blog posts**: `data/blog/**/*.mdx` (and `.md`) → `Blog` document type
- **Authors**: `data/authors/**/*.mdx` → `Authors` document type
- contentlayer2 compiles MDX to typed JSON output in `.contentlayer/generated/`
- `onSuccess` hook generates:
  1. `app/tag-data.json` — tag counts
  2. `public/search.json` — kbar local search index (when kbar is configured)

### Next.js App Router

Route structure in `app/`:
- `app/page.tsx` — Home page
- `app/blog/page.tsx` — Blog listing
- `app/tags/page.tsx` — Tag cloud
- `app/about/page.tsx` — About page
- `app/projects/page.tsx` — Projects page
- `app/seo.tsx` — Shared SEO component
- `app/sitemap.ts` / `app/robots.ts` — SEO metadata

### Key Directories

- `layouts/` — Post rendering layouts (`PostLayout`, `PostBanner`, `PostSimple`, `ListLayout`, `ListLayoutWithTags`, `AuthorLayout`)
- `components/` — Shared UI components (`Header`, `Footer`, `MDXComponents`, `ThemeSwitch`, `MobileNav`, `Card`, `Tag`, `Comments`, etc.)
- `data/` — Content files + config (`siteMetadata.js`, `headerNavLinks.ts`, `projectsData.ts`)

### Configuration Files

- `contentlayer.config.ts` — Document type definitions, MDX remark/rehype plugins, post-build hooks
- `next.config.js` — Wrapped with `withContentlayer` + `withBundleAnalyzer`, CSP headers, SVG via `@svgr/webpack`
- `data/siteMetadata.js` — Global site metadata, analytics, comments, search providers

## Blog Post Frontmatter

```yaml
---
title: 'Article Title'
date: '2024-12-04'
tags:
  - tag1
draft: false          # Hidden in production when true
summary: 'Summary text'
images: []            # For og:image
authors:              # Optional, defaults to data/authors/default.mdx
  - default
layout: PostLayout    # Optional: PostLayout | PostBanner | PostSimple
bibliography: references-data.bib  # Optional
canonicalUrl: ''      # Optional
---
```

Slug is auto-computed from file path (strips `blog/` prefix). Filenames can be Chinese but beware URL encoding.

## MDX Enhancements

- **Math**: KaTeX (`$...$` inline, `$$...$$` block)
- **Code block titles**: `` ```js:filename.js ``
- **GitHub alerts**: `> [!NOTE]`, `> [!WARNING]`
- **Citations**: `rehype-citation`, put `.bib` files in `data/`
- **Image optimization**: `remarkImgToJsx` auto-converts `img` to Next.js `<Image>`

## Code Style

- Prettier: no semicolons, single quotes, 100 char line width, `es5` trailing comma, `prettier-plugin-tailwindcss`
- ESLint: TypeScript + jsx-a11y + Next.js + prettier
- Pre-commit hooks: husky + lint-staged auto-format

## Adding Authors

Create `.mdx` file in `data/authors/` with frontmatter: `name`, `avatar`, `occupation`, `company`, `email`, `github`, `layout` (default: `AuthorLayout`).

## Writing New Blog Posts

Create `.md` or `.mdx` files in `data/blog/` with required frontmatter (`title`, `date`). The dev server auto-updates on save.
