# GOTCHAS.md

Hard-won workflow gotchas for this repository. Read this before writing commit messages, PR/issue bodies, or comments — especially anything that references the upstream repository.

## Referencing upstream issues/PRs creates notifications on their side

This repo is a fork of `yutto-dev/yutto`. GitHub autolinks references like `yutto-dev/yutto#743` in commit messages, PR bodies, and comments — and every such reference posts a "mentioned this" event on the upstream item's timeline. From a fork that does frequent syncs and prototyping, this quickly becomes noise (打扰) for the upstream maintainers, and the events cannot be retracted by editing afterwards.

Rules:

- Never write `yutto-dev/yutto#N` (the `owner/repo#N` shorthand) anywhere in this repo — commits, PR bodies, PR/issue comments.
- When a reference is genuinely needed, use a plain URL instead: `https://github.com/yutto-dev/yutto/pull/743`.
- When you must guarantee zero upstream notification (e.g. a sync PR that mentions many upstream PRs), wrap the URL in backticks so GitHub does not autolink it at all.
- Bare `#N` always refers to THIS repo's numbering — only use it for this repo's own issues/PRs.

## Windows PowerShell redirection corrupts `gh` body files

Windows PowerShell 5.1 writes `>` / `Out-File` output as UTF-16 LE. If a file that will be passed to `gh pr create/edit/comment --body-file` was ever created or touched by a PowerShell redirect, `gh` uploads UTF-16 bytes as UTF-8 and all Chinese text renders as mojibake on GitHub.

Rules:

- Author `--body-file` content as a fresh UTF-8 file (e.g. via an editor or agent Write tool), never via PowerShell redirection, and never reuse a file path that a redirect ever touched.
- After any `gh pr edit` / `gh issue edit` / `gh pr comment`, fetch the body back (`gh pr view --json body`) and confirm the Chinese renders correctly before reporting done.
