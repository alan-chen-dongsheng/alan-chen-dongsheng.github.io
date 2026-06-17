---
title: 'Claude Code 技巧学习'
date: '2026-04-26'
tags:
  - Claude Code
  - AI
  - 编程工具
draft: false
summary: 'Claude Code 的实用技巧和常用命令学习。'
---

# Claude Code 技巧学习

# 文件结构



## 项目级别

```shell
your-project/
├── CLAUDE.md                    # 📋 项目级指令（团队共享，提交到 Git）
├── CLAUDE.local.md              # 👤 个人项目偏好（自动 gitignore）
├── .claude/
│   ├── settings.json            # ⚙️ 项目设置（团队共享）
│   ├── settings.local.json      # 👤 个人项目设置（gitignore）
│   ├── CLAUDE.md                # 📋 等效于根目录 CLAUDE.md
│   ├── rules/                   # 📏 模块化规则文件
│   │   ├── code-style.md        #    代码风格
│   │   ├── testing.md           #    测试规范
│   │   └── security.md          #    安全要求
│   ├── agents/                  # 🤖 自定义子代理
│   │   ├── code-reviewer.md
│   │   └── debugger.md
│   ├── skills/                  # ⚡ 自定义技能
│   │   └── fix-issue/
│   │       └── SKILL.md
│   └── worktrees/               # 🌳 Git Worktree 目录（加入 .gitignore）
├── .mcp.json                    # 🔌 项目级 MCP 服务器配置
```



## 开发理念

### 1. **规范驱动开发（Spec-Driven Development, SDD）** 

```text
specs/001-feature-name/
├── spec.md      ← WHAT：功能需求（用户故事、验收标准、边界情况）
├── plan.md      ← HOW：技术方案（架构设计、数据结构、接口定义）
└── tasks.md     ← DO：原子任务（逐步执行指令，每个任务改一个文件）
```

| 产物     | 定位                 | 核心内容                                         | 谁来写                    |
| -------- | -------------------- | ------------------------------------------------ | ------------------------- |
| spec.md  | 需求规范（WHAT/WHY） | 用户故事、验收标准、边界情况、MVP 范围           | 你主导，Claude 辅助提问   |
| plan.md  | 技术方案（HOW）      | 技术选型、目录结构、数据模型、接口设计、风险评估 | Claude 主导，你审核决策   |
| tasks.md | 执行计划（DO）       | 原子化任务列表、依赖关系、TDD 顺序               | Claude 生成，你审核完整性 |

**第一步：协作编写 spec.md**

```text
> 我想构建 [功能描述]。用采访模式对我进行详细提问，
> 帮我生成一份 spec.md，包含：用户故事、验收标准、边界情况。
> 不要写任何技术实现细节。
```

**第二步：生成 plan.md**

```text
> @specs/001-feature/spec.md
> 基于这份需求规范，生成技术方案 plan.md。
> 技术栈约束：[TypeScript / React / PostgreSQL]
> 包含：目录结构、核心数据模型、接口定义、实施阶段。
```

**第三步：分解 tasks.md**

```text
> @specs/001-feature/spec.md @specs/001-feature/plan.md
> 将技术方案分解为原子任务列表 tasks.md。
> 要求：每个任务只改一个文件，测试先行（奇数任务写测试，偶数任务写实现）。
```

**第四步：逐步执行**

```text
> @specs/001-feature/tasks.md
> 执行任务 T001-T006。严格按 TDD 顺序：先写测试（必须失败），再写实现（使测试通过）。
```

### 2. TDD 











# 其它

## 有用的命令

```shell
# 用于查看我目前使用 Claude Code 的方法
/insights

# 消耗多少 key
/cost

# 检查目前使用了什么信息，占用 token 的信息
# 排除加载了不用的插件占用了 tokens
/context

# 压缩信息
/compact

/agents 查看子代理, 或者新增子代理

claude --worktree feature-auth # 新建一个worktree用于任务
# 最好自己手动创建worktree,这样修改起来会比较自由,比如:
git worktree add ../project-feature-a -b feature-a
git worktree add ../project-bugfix bugfix-123
git worktree list
```



- 

```shell
cat data.txt | claude -p 'summarize this data' --output-format text > summary.txt
```





## 新增 MCP 服务

- github
- Context7

```shell
/mcp # show all mcp server

mcp 3 level:
1. project level
2. user level
3. global level
```

## Skill

