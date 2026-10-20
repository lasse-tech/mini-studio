"""Print the hash of main rewritten without the private top-level files.

Every commit keeps its message, author, committer and dates, so the rewrite is
deterministic: the same history gives the same hashes, and pushing it again is
a fast-forward. Commits that only touched private files are dropped.
"""

from __future__ import annotations

import os
import subprocess
import sys


def git(*args: str, data: str | None = None, env: dict | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        input=data,
        env=env,
        text=True,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def main() -> None:
    ref, private = sys.argv[1], set(sys.argv[2:])
    mapped: dict[str, str] = {}
    trees: dict[str, str] = {}
    head = ""
    for line in git(
        "rev-list", "--topo-order", "--reverse", "--parents", ref
    ).splitlines():
        commit, *parents = line.split()
        entries = git("ls-tree", "-z", commit).split("\0")
        kept = [e for e in entries if e and e.split("\t", 1)[1] not in private]
        tree = git("mktree", "-z", data="\0".join(kept) + "\0" if kept else "")
        new_parents = list(dict.fromkeys(mapped[p] for p in parents))
        if len(new_parents) == 1 and trees[new_parents[0]] == tree:
            mapped[commit] = new_parents[0]
            continue
        fields = git(
            "log",
            "-1",
            "--format=%an%x00%ae%x00%ad%x00%cn%x00%ce%x00%cd",
            "--date=raw",
            commit,
        ).split("\0")
        env = dict(
            os.environ,
            GIT_AUTHOR_NAME=fields[0],
            GIT_AUTHOR_EMAIL=fields[1],
            GIT_AUTHOR_DATE=fields[2],
            GIT_COMMITTER_NAME=fields[3],
            GIT_COMMITTER_EMAIL=fields[4],
            GIT_COMMITTER_DATE=fields[5],
        )
        message = git("log", "-1", "--format=%B", commit) + "\n"
        args = ["commit-tree", tree]
        for parent in new_parents:
            args += ["-p", parent]
        head = mapped[commit] = git(*args, "-F", "-", data=message, env=env)
        trees[head] = tree
    print(head)


if __name__ == "__main__":
    main()
