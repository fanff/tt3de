# AGENT.md

## Test Command Guidance

When running tests, set `PYTHONPATH` to the repository root so imports like `tests.*` resolve correctly.

- On **Windows (PowerShell)**, run tests with:

```powershell
$env:PYTHONPATH='.'; uv run pytest <test-path-or-args>
```

- On **macOS/Linux (bash/zsh)**, use the shell equivalent:

```bash
PYTHONPATH=. uv run pytest <test-path-or-args>
```

## OS Awareness

Always detect or confirm the operating system before suggesting or running commands.

- Use the PowerShell form on Windows.
- Use the bash/zsh form on macOS or Linux.
- Do not assume one shell syntax works on all platforms.

## Development-Only Script

The script `tt3de-gen-opcodes` is defined in `pyproject.toml` and is intended for development workflows only.

- Treat `tt3de-gen-opcodes` as a dev tool.
- It must **not** be deployed or shipped inside released packages.

## Branch and Commit Strategy

Before starting new feature/chore work, update your local base from `master` (for example: pull latest `master` first, then branch).

- Branch naming should usually follow:
  - `feat/<short-description>`
  - `chore/<short-description>`
- Commit messages must follow release-standard Conventional Commits, such as:
  - `feat: <what changed>`
  - `chore: <what changed>`
  - `fix: <what changed>`
  - `docs: <what changed>`
- Keep commit message prefixes consistent so release automation and changelog tooling remain reliable.

### Example Command Sequence (Windows PowerShell)

```powershell
git checkout master
git pull
git checkout -b feat/<short-description>
git add .
git commit -m "feat: <what changed>"
```
