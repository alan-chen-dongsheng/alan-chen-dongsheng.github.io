---
title: 'Git worktree 详解：多分支并行开发的高效解决方案（含实操示例）'
date: '2026-03-01'
tags:
  - git
draft: false
summary: '详解Git worktree用法，解决多分支并行开发痛点，附实操示例。'
---

# 一、什么是 Git worktree

Git worktree 是 Git 2.5.0 版本引入的核心功能，用于在本地文件系统的不同目录中，同时检出同一个 Git 仓库的不同分支。简单来说，它允许你在不切换当前仓库分支、不 stash 或 commit 未完成代码的前提下，在另一个文件夹中操作仓库的其他分支，实现“多分支并行开发”。

核心特点：多个工作目录共享同一个 Git 仓库（.git 文件夹），无需重复克隆仓库，节省磁盘空间；各工作目录独立操作，互不影响，避免了频繁切换分支时的代码冲突、未提交代码丢失等问题。

# 二、Git worktree 用来解决什么问题

在日常 Git 开发中，我们经常会遇到以下痛点，而 worktree 正是为解决这些问题而生：

1. **未提交代码时，无法切换分支**：当你在某个分支（如 dev）写了代码但未 git add/git commit 时，直接切换到其他分支（如 master）会被 Git 阻止（避免未提交代码被覆盖），此时只能通过 git stash 暂存代码，切换分支完成操作后再 stash pop 恢复，步骤繁琐且容易出错。
2. **多分支并行开发效率低**：如果需要同时处理多个任务（如一边开发 dev 分支的新功能，一边修复 master 分支的紧急 bug），传统方式只能反复切换分支、暂存/恢复代码，频繁的上下文切换会降低开发效率。
3. **重复克隆仓库浪费资源**：若为了并行操作不同分支而多次克隆同一个仓库，会占用大量磁盘空间，且多个仓库间无法共享提交记录，同步分支时需要额外操作。

worktree 通过“一个仓库、多个工作目录”的模式，完美解决了以上问题，让多分支并行开发更高效、更便捷。

# 三、Git worktree 如何使用（核心命令）

Git worktree 的使用主要围绕 3 个核心命令：创建 worktree、查看 worktree、删除 worktree，以下是详细说明（所有命令均在 Git 仓库根目录执行）。

## 1. 查看当前仓库的 worktree 列表

命令：`git worktree list`

作用：查看当前 Git 仓库关联的所有工作目录，包括每个工作目录的路径、对应的分支，以及是否为“锁定状态”（锁定状态下无法删除 worktree）。

## 2. 创建 worktree（核心命令）

命令：`git worktree add <工作目录路径> <分支名>`

参数说明：

- `<工作目录路径>`：指定新 worktree 的存放位置（建议在仓库根目录外创建，避免嵌套，如 ../bugfix-worktree）；
- `<分支名>`：指定要检出的分支（可以是已存在的分支，如 master，也可以是新建分支，格式为 `<新分支名>` `<基准分支名>`）。

补充：若需基于某个分支新建分支并创建 worktree，可直接执行：`git worktree add <工作目录路径> <新分支名> -b <基准分支名>`（-b 表示新建分支）。

## 3. 删除 worktree

命令：`git worktree remove <工作目录路径>`

作用：删除指定的 worktree 工作目录，同时解除其与 Git 仓库的关联。

注意：若 worktree 目录中存在未提交的更改，删除时会提示报错，需先提交或放弃更改；若 worktree 处于锁定状态，需先执行 `git worktree unlock <工作目录路径>` 解锁，再删除。

## 4. 解锁 worktree（可选）

命令：`git worktree unlock <工作目录路径>`

作用：当 worktree 意外崩溃或锁定时，解锁后才能进行删除操作。

# 四、实操示例（贴合你的场景）

场景：当前在 dev 分支开发，已写部分代码但未执行 git add，需要基于 master 分支新建 bugfix 分支（bugfix-compiler-234-fix-parse-error），创建 worktree 用于修改 bug，完成后提交并删除 worktree。

前提：当前所在目录为 Git 仓库根目录，当前分支为 dev，且存在未 add 的代码（无需 stash，直接操作）。

## 步骤 1：查看当前分支和 worktree 状态

执行命令，确认当前分支和 worktree 列表（初始无额外 worktree）：

```bash
# 查看当前分支
git branch
# 查看当前 worktree 列表（初始为空，仅显示当前仓库目录）
git worktree list
```

输出说明：git branch 会显示当前分支为 dev，且有未提交的更改提示；git worktree list 仅显示当前仓库的路径和 dev 分支。

## 步骤 2：基于 master 分支，新建 bugfix 分支并创建 worktree

执行命令，在仓库根目录外创建 worktree 目录（避免嵌套），同时新建 bugfix 分支（基于 master）：

```bash
# 格式：git worktree add <worktree路径> <新bugfix分支名> -b <基准分支master>
git worktree add ../bugfix-compiler-234 bugfix-compiler-234-fix-parse-error -b master
```

说明：

- ../bugfix-compiler-234：worktree 存放路径（在当前仓库上一级目录，创建名为 bugfix-compiler-234 的文件夹）；
- bugfix-compiler-234-fix-parse-error：新建的 bugfix 分支名；
- -b master：表示新建的 bugfix 分支，以 master 为基准（即基于 master 分支的最新代码创建）。

执行成功后，会自动进入 worktree 目录（../bugfix-compiler-234），且当前分支为新建的 bugfix 分支，此时 master 分支的代码已完整检出，与 dev 分支的未提交代码完全隔离。

## 步骤 3：在 worktree 中修改 bug 并提交

在 worktree 目录（../bugfix-compiler-234）中，编辑代码修复 parse error 问题，完成后执行提交操作：

```bash
# 1. 进入 worktree 目录（若未自动进入）
cd ../bugfix-compiler-234
# 2. 查看修改的文件
git status
# 3. 暂存修改（git add）
git add .
# 4. 提交修改（填写提交信息，说明修复的问题）
git commit -m "fix: compiler parse error (bug #234)"
# 5. （可选）将 bugfix 分支推送到远程仓库
git push origin bugfix-compiler-234-fix-parse-error
```

注意：此过程中，原 dev 分支的未提交代码不受任何影响，无需 stash，原仓库目录的 dev 分支依然保持原样。

## 步骤 4：删除 worktree（bugfix 完成后）

bug 修复并提交后，删除 worktree 目录（解除与原仓库的关联），回到原仓库继续开发 dev 分支：

```bash
# 1. 回到原 Git 仓库根目录（退出 worktree 目录）
cd ../你的原仓库目录
# 2. 查看当前 worktree 列表，确认要删除的 worktree 路径
git worktree list
# 3. 删除 worktree（路径为之前创建的 ../bugfix-compiler-234）
git worktree remove ../bugfix-compiler-234
```

删除成功后，../bugfix-compiler-234 目录会被删除，git worktree list 中不再显示该 worktree；新建的 bugfix 分支依然存在（本地和远程，若已推送），后续可根据需求合并到 master 分支。

## 步骤 5：回到 dev 分支继续开发

删除 worktree 后，原仓库的 dev 分支依然保留着之前未 add 的代码，可继续开发、add、commit，无需任何额外恢复操作。

# 五、Git worktree 总结

## 1. 核心价值

Git worktree 的核心是“共享仓库、独立工作目录”，解决了多分支并行开发时“未提交代码无法切换分支”“频繁 stash 繁琐”“重复克隆浪费资源”的痛点，尤其适合需要同时处理多个任务（如开发新功能+修复紧急 bug）的场景。

## 2. 优势

- 高效：无需切换分支、暂存代码，多分支并行开发，减少上下文切换成本；
- 节省空间：多个工作目录共享一个 .git 仓库，无需重复克隆；
- 安全：各工作目录独立操作，避免未提交代码被覆盖或丢失。

## 3. 注意事项

- worktree 目录建议不要嵌套在原仓库目录中，避免冲突；
- 删除 worktree 前，需确保 worktree 中无未提交的更改（或已放弃更改），否则会报错；
- worktree 仅关联本地分支，远程分支的推送/拉取需在 worktree 目录中正常执行；
- Git 版本需 ≥ 2.5.0，若版本过低，需先升级 Git（如 `git update-git-for-windows` 或通过包管理器升级）。

## 4. 适用场景

适合多分支并行开发、紧急 bug 修复（不影响当前开发分支）、代码评审（单独检出分支查看）等场景，是提升 Git 开发效率的实用工具。