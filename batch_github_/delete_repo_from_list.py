#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error

GHTOKEN = os.environ.get("GHTOKEN", "").strip()
LIST_FILE = "repos_all.txt"  # each line: owner/repo
API = "https://api.github.com"


def load_repos(path: str):
    repos = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            repos.append(line)
    # de-dup while preserving order
    seen = set()
    uniq = []
    for r in repos:
        if r not in seen:
            uniq.append(r)
            seen.add(r)
    return uniq


def gh_request(method: str, url: str):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GHTOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "delete-repos-script",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
            return status, raw
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8", errors="replace")
        return status, raw
    except Exception as e:
        return 0, str(e)


def main():
    if not GHTOKEN:
        print(
            "Missing GHTOKEN env var.\n"
            "Example:\n"
            "  export GHTOKEN='github_pat_...'\n"
            "  python3 delete_repos_from_list.py",
            file=sys.stderr,
        )
        sys.exit(2)

    repos = load_repos(LIST_FILE)
    if not repos:
        print(f"No repos found in {LIST_FILE}.")
        return

    print(f"About to DELETE {len(repos)} repositories listed in {LIST_FILE}:")
    for i, r in enumerate(repos, 1):
        print(f"{i:4d}. {r}")
    print()
    confirm = input("Type DELETE to continue: ").strip()
    if confirm != "DELETE":
        print("Abort.")
        sys.exit(1)

    ok = 0
    fail = 0

    for r in repos:
        url = f"{API}/repos/{r}"
        status, raw = gh_request("DELETE", url)

        if status == 204:
            ok += 1
            print(f"OK    (204): {r}")
            continue

        fail += 1
        print(f"FAIL  ({status}): {r}")
        # try to format GitHub error JSON
        try:
            obj = json.loads(raw) if raw else {}
            msg = obj.get("message") or raw
            print(f"  message: {msg}")
            if "documentation_url" in obj:
                print(f"  documentation_url: {obj['documentation_url']}")
        except Exception:
            if raw:
                print(f"  response: {raw[:500]}")
        print()

    print(f"Done. OK={ok}, FAIL={fail}")


if __name__ == "__main__":
    main()
