---
name: sync-upstream
description: Sync the local master branch with the upstream repository (timlrx/tailwind-nextjs-starter-blog main branch) and resolve conflicts. Use this when asked to sync, update, or merge upstream changes.
---

This project is forked from https://github.com/timlrx/tailwind-nextjs-starter-blog. The upstream remote should point to that repository.

## Steps to sync upstream

1. **Ensure the upstream remote URL is correct:**
   ```bash
   git remote set-url upstream https://github.com/timlrx/tailwind-nextjs-starter-blog.git
   ```
   If the remote doesn't exist yet, add it:
   ```bash
   git remote add upstream https://github.com/timlrx/tailwind-nextjs-starter-blog.git
   ```

2. **Fetch the latest upstream changes:**
   ```bash
   git fetch upstream
   ```

3. **Merge upstream/main into the local master branch:**
   ```bash
   git merge upstream/main --no-edit
   ```

4. **If conflicts arise, resolve them using these rules:**

   | File | Resolution |
   |------|-----------|
   | `package.json` | Use **upstream** version (get the latest dependency updates) |
   | `yarn.lock` | Keep **ours** (will be rebuilt locally with `yarn install`) |
   | `app/tag-data.json` | Keep **ours** (auto-generated from our blog posts) |
   | `data/**` | Keep **ours** (our own blog content and configuration) |
   | `data/siteMetadata.js` | Keep **ours** (our site configuration) |
   | Other files | Use judgment: prefer upstream for framework files, ours for customized content |

   To resolve using the rules above:
   ```bash
   # Use upstream version
   git checkout upstream/main -- package.json

   # Keep our version
   git checkout HEAD -- yarn.lock
   git checkout HEAD -- app/tag-data.json
   ```

5. **Stage resolved files and complete the merge:**
   ```bash
   git add -A
   git commit --no-edit
   ```

6. **After merging, if `package.json` was updated, reinstall dependencies:**
   ```bash
   yarn install
   ```
