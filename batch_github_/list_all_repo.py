#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error

GHTOKEN = os.environ.get("GHTOKEN", "").strip()

OUT_FILE = "repos_all.txt"
PER_PAGE = 100


def request_json(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GHTOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "export-all-repos-script",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {status} for {url}\n{raw[:1000]}")
    except Exception as e:
        raise RuntimeError(f"Request failed for {url}: {e}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Non-JSON response for {url} (HTTP {status}). First 1000 chars:\n{raw[:1000]}"
        )
    return status, data


def main():
    if not GHTOKEN:
        print(
            "Missing GHTOKEN env var.\n"
            "Example:\n"
            "  export GHTOKEN='github_pat_...'\n"
            "  python3 export_all_repos.py",
            file=sys.stderr,
        )
        sys.exit(2)

    page = 1
    names = set()

    while True:
        url = (
            "https://api.github.com/user/repos"
            f"?per_page={PER_PAGE}&page={page}"
            "&sort=full_name&direction=asc"
            "&visibility=all"
            "&affiliation=owner,collaborator,organization_member"
        )
        _, data = request_json(url)

        if not isinstance(data, list):
            raise RuntimeError(
                f"Unexpected response type on page {page}: {type(data)}\n{str(data)[:1000]}"
            )

        if not data:
            break

        for repo in data:
            full_name = repo.get("full_name")
            if full_name:
                names.add(full_name)

        page += 1

    out = sorted(names)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + ("\n" if out else ""))

    print(f"Saved: {OUT_FILE}")
    print(f"Repo count: {len(out)}")
    print("Preview (first 30):")
    for line in out[:30]:
        print(line)


if __name__ == "__main__":
    main()
