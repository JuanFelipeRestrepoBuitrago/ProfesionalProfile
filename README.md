# Professional Profile Manager

An AI-assisted workspace for maintaining a software engineer's professional
profile end to end: canonical CVs (English + Spanish), polished Word/PDF exports
in multiple visual formats, and a LinkedIn profile kept in sync — all driven
from a single source of truth.

The AI assistant works as a **senior technical recruiter and career document
partner**: it maintains verified facts, writes recruiter-grade copy, and never
fabricates roles, metrics, or credentials.

## Purpose

- Keep `cv.md` (English) and `cv_es.md` (Spanish) as the single authoritative
  record of the professional profile.
- Generate styled CV documents (Word/PDF) in several layouts from those sources,
  without hand-editing binary files.
- Convert incoming PDF/Word CVs into clean Markdown.
- Align the LinkedIn profile with the canonical CVs.
- Make the whole AI setup **portable** across Kiro, Claude Code, and Codex via
  [APM](https://github.com/microsoft/apm) (Agent Package Manager): `.apm/` plus
  `apm.yml` are the single source, and `apm install` deploys each tool's config.

## Repository structure

```
.
├── apm.yml               # APM manifest: targets + MCP dependencies (tracked)
├── .apm/                 # APM source of truth for AI configuration (tracked)
│   ├── instructions/     #   always-on behavioral rules (*.instructions.md)
│   └── skills/           #   skill definitions (+ scripts/templates)
├── .kiro/                # Generated Kiro config (git-ignored)
├── cv.md                 # Canonical CV — English (git-ignored: personal data)
├── cv_es.md              # Canonical CV — Spanish (git-ignored: personal data)
├── cv_formats/           # Styled .docx design references (git-ignored)
├── resources/            # Images used in CVs (e.g. DEFAULT.jpg headshot)
├── results/              # Generated / tailored CV outputs (git-ignored)
├── .gitignore
└── README.md
```

What is tracked in git: `apm.yml`, `.apm/`, `resources/`, this README, and
`.gitignore`. Everything that is generated, personal, or machine-specific is
ignored (see `.gitignore`). `apm.yml` + `.apm/` are the only place you edit AI
configuration; the per-tool folders (`.kiro/`, `.claude/`, `.codex/`) are
generated from them by `apm install`.

Mapping from APM source to each tool's native config:

| APM source                      | Kiro                      | Claude Code       | Codex                  |
| ------------------------------- | ------------------------- | ----------------- | ---------------------- |
| `.apm/instructions/*.md`        | `.kiro/steering/*.md`     | `.claude/rules/*` | `AGENTS.md`            |
| `.apm/skills/<name>/`           | `.kiro/skills/<name>/`    | `.claude/skills/` | `.agents/skills/`      |
| `apm.yml` → `dependencies.mcp:` | `.kiro/settings/mcp.json` | `.mcp.json`       | `~/.codex/config.toml` |

## Prerequisites

The skills rely on four MCP servers. Install their runtimes once per machine.

| MCP server        | Provides                           | Needs                                 |
| ----------------- | ---------------------------------- | ------------------------------------- |
| `document-loader` | PDF/DOCX/DOC → text extraction     | `uv` / `uvx`                          |
| `linkedin`        | Read-only LinkedIn profile queries | `uv` / `uvx` (+ LinkedIn session)     |
| `office-mcp`      | Word/Excel/PPTX read + PDF export  | Python 3.10+, LibreOffice (`soffice`) |
| `engram`          | Persistent cross-session memory    | `engram` binary on `PATH`             |

Core requirements:

- **Python 3.10+** — runs the CV generator script and the office MCP.
- **uv / uvx** — launches the `uvx`-based MCP servers (downloads them on first run).
- **LibreOffice** — headless `soffice` is used to export generated `.docx` to PDF.
- **APM** ([Agent Package Manager](https://github.com/microsoft/apm)) — deploys
  the `.apm/` + `apm.yml` source into each tool's config (`apm install`).
- **An AI tool** — Kiro, Claude Code, or Codex. The repo ships a single APM
  source of truth; `apm install` generates the config for whichever you use.

The `uvx`-based servers (`document-loader`, `linkedin`) are fetched on first
run by `uvx` — there is nothing to install for them beyond `uv` itself. `apm`
writes each server's launch command into the harness config; it does **not**
install the programs those commands invoke, so install the runtimes below once
per machine.

### Install (Linux — Ubuntu/Debian)

```bash
# 1. Python 3.10+ and LibreOffice (headless soffice for DOCX → PDF export)
sudo apt update
sudo apt install -y python3 python3-pip python3-venv libreoffice

# 2. uv / uvx (standalone installer — ships both binaries)
curl -LsSf https://astral.sh/uv/install.sh | sh
#   installs to ~/.local/bin — restart the shell or:
source "$HOME/.local/bin/env"        # ensures uv + uvx are on PATH

# 3. office-mcp — the launch command expects a venv at ~/tools/office-mcp/
git clone <office-mcp-repo> ~/tools/office-mcp
python3 -m venv ~/tools/office-mcp/.venv
~/tools/office-mcp/.venv/bin/pip install -r ~/tools/office-mcp/requirements.txt

# 4. engram (persistent-memory MCP) — expected at ~/.local/bin/engram.
#    Install the Engram CLI per its own docs, then confirm it's reachable:
command -v engram
```

### Install (macOS)

```bash
# 1. Homebrew packages — python, LibreOffice, and uv (uvx ships with uv)
brew install python libreoffice uv

# 2. office-mcp venv at ~/tools/office-mcp/
git clone <office-mcp-repo> ~/tools/office-mcp
python3 -m venv ~/tools/office-mcp/.venv
~/tools/office-mcp/.venv/bin/pip install -r ~/tools/office-mcp/requirements.txt

# 3. engram — install the Engram CLI, then verify:
command -v engram
```

> On Apple Silicon, Homebrew lives at `/opt/homebrew/bin`; make sure it's on
> your `PATH` so `soffice`, `uv`, and `uvx` resolve.

### Install (Windows)

The office MCP paths in `apm.yml` use POSIX layout (`${HOME}/tools/office-mcp/...`),
so **WSL (Ubuntu)** is the smoothest path — install WSL, then follow the Linux
steps verbatim inside it:

```powershell
wsl --install -d Ubuntu      # then open the Ubuntu shell and use the Linux steps
```

To run natively in PowerShell instead, install the runtimes with winget and
adjust the `office-mcp` `command`/`args` paths in `apm.yml` to Windows paths:

```powershell
# winget packages
winget install --id Python.Python.3.12 -e
winget install --id TheDocumentFoundation.LibreOffice -e
winget install --id astral-sh.uv -e      # provides uv + uvx

# office-mcp venv (adjust apm.yml paths to match)
git clone <office-mcp-repo> $HOME\tools\office-mcp
python -m venv $HOME\tools\office-mcp\.venv
$HOME\tools\office-mcp\.venv\Scripts\pip install -r $HOME\tools\office-mcp\requirements.txt
```

Then confirm `uv`, `uvx`, `python`, `soffice`, and `engram` are all on your
`PATH`.

### Verify

```bash
python3 --version
uv --version && uvx --version
soffice --version        # or: libreoffice --version
engram --version         # only if using the memory MCP
apm --version            # APM CLI, used to deploy the AI config
```

## Configuring the AI tools

All configuration lives in `apm.yml` + `.apm/` and is deployed into each tool's
native folders by [APM](https://github.com/microsoft/apm). You do not copy files
by hand — `apm install` reads the manifest and generates the Kiro, Claude, and
Codex configs in one step.

### Install APM once per machine

```bash
# APM CLI (see https://github.com/microsoft/apm for alternatives)
pip install apm-cli        # or: pipx install apm-cli
apm --version
```

### Deploy the config

From the repo root:

```bash
# Deploy to every target listed in apm.yml (kiro, claude, codex)
apm install

# Or scope to a single tool
apm install --target kiro
apm install --target claude
apm install --target codex
```

This regenerates `.kiro/`, `.claude/`, and `.codex/` (plus `.mcp.json` /
`AGENTS.md`) and writes the four MCP servers into each tool's MCP config. After
editing anything under `.apm/` or `apm.yml`, re-run `apm install` to refresh the
generated folders.

```bash
# Preview without writing, or validate the APM primitives
apm install --dry-run
apm compile --validate
```

### Environment variables

`apm` keeps every env value in `apm.yml` as a `${VAR}` placeholder and writes
those placeholders into the generated MCP config (`.kiro/settings/mcp.json`,
`.mcp.json`, …). **The placeholders are never turned into literals on disk** —
re-running `apm install` always regenerates them. Each `${VAR}` is resolved by
the AI tool **when it launches the MCP server**, reading the value from the
environment of the process that started the tool. So the values must be exported
in the shell (or login environment) that launches Kiro / Claude / Codex.

Two kinds of variables are used:

| Variable            | Used by           | Set it yourself? | Notes                                                                                                                       |
| ------------------- | ----------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `HOME`              | `office-mcp`, …   | No               | Provided by the OS                                                                                                          |
| `PROJECT_ROOT`      | `office-mcp`      | No               | Injected per-workspace by the AI tool — keep it a placeholder so the config stays portable when you open the repo elsewhere |
| `FASTMCP_LOG_LEVEL` | `document-loader` | Yes              | `ERROR`                                                                                                                     |
| `UV_HTTP_TIMEOUT`   | `linkedin`        | Yes              | `300` (seconds)                                                                                                             |
| `PYTHONUTF8`        | `office-mcp`      | Yes              | `1`                                                                                                                         |
| `PYTHONIOENCODING`  | `office-mcp`      | Yes              | `utf-8`                                                                                                                     |

Do **not** hardcode `HOME` or `PROJECT_ROOT`: the AI tool supplies them at
runtime from the current workspace, which is what lets the same config work no
matter where you clone or open the repo. Only the four fixed-value variables
below need exporting.

#### Linux (zsh — `~/.zshrc`)

```zsh
# ~/.zshrc — add these, then: source ~/.zshrc
export FASTMCP_LOG_LEVEL=ERROR
export UV_HTTP_TIMEOUT=300
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

For bash, put the same `export` lines in `~/.bashrc` instead.

#### macOS (zsh — `~/.zshrc`)

macOS uses zsh by default, so the lines are identical:

```zsh
# ~/.zshrc — add these, then: source ~/.zshrc
export FASTMCP_LOG_LEVEL=ERROR
export UV_HTTP_TIMEOUT=300
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

#### Windows (PowerShell)

Set them as persistent user environment variables (survives reboots), then
restart the terminal / AI tool so they're inherited:

```powershell
[Environment]::SetEnvironmentVariable('FASTMCP_LOG_LEVEL', 'ERROR', 'User')
[Environment]::SetEnvironmentVariable('UV_HTTP_TIMEOUT', '300', 'User')
[Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', 'User')
[Environment]::SetEnvironmentVariable('PYTHONIOENCODING', 'utf-8', 'User')
```

Running inside **WSL (Ubuntu)**? Use the Linux (zsh/bash) steps instead.

The remaining MCP paths are derived from `HOME`: the `engram` binary is taken
from `PATH`, and the office MCP runs from `${HOME}/tools/office-mcp/`
(`.venv/bin/python` + `server.py`). Adjust those paths in `apm.yml` if your
layout differs.

Never put secrets or access tokens in config files — use environment variables.

## Skills and what you can do with them

Skills are task playbooks the assistant follows. Five ship with this repo:

### `update-canonical-cv`

Updates the canonical sources with new verified details (role, project, skill,
certification, education, contact). **Always edits both** `cv.md` and `cv_es.md`
so English and Spanish stay in sync. Does not invent facts.

> "Add my new role as Staff Engineer at Acme, starting Jan 2026."

### `generate-cv-document`

Produces a polished CV from the canonical sources in a chosen **language**
(`en`/`es`), **format** (`ats`, `general`, or any added format), and
**extension** (`word` by default, `pdf` on request). Fills a styled template so
the exact fonts/colors/layout are preserved regardless of how many jobs or
bullets you have. Photo formats pull the headshot from `resources/`
(`DEFAULT.jpg` by default). Output lands in `results/`.

> "Make my English CV in the ATS format." ·
> "Export my Spanish CV as PDF in the general format using headshot.jpg."

### `add-cv-template`

Turns a styled `.docx` you drop into `cv_formats/` into a reusable,
generator-ready template — tokenizing the text while preserving every font,
color, border, and image — then wires it into `generate-cv-document` and
verifies it round-trips. Use when adding a new CV design.

> "I added `cv_formats/modern.docx` — make it a format I can generate."

### `document-to-markdown`

Converts a PDF or Word CV into clean, structured Markdown using the
`document-loader` MCP (faithful extraction, no rewriting or invention). Useful
for seeding a new `cv.md` / `cv_es.md` from an existing document.

> "Here's my old CV as a PDF — convert it to Markdown."

### `sync-linkedin-profile`

Queries the current LinkedIn profile (read-only MCP), compares it against the
canonical CVs, and writes recruiter-grade replacement copy for every section to
`results/linkedin.md`. **LinkedIn is read-only** — the file is a manual-apply
handoff; the assistant never edits LinkedIn directly.

> "Refresh my LinkedIn to match my CV."

## Behavioral rules (steering)

Always-on rules in `.apm/instructions/` shape every interaction:

- **role** — senior technical recruiter persona; never fabricate; recruiter-grade
  professional writing standard.
- **language** — reply in the user's language; keep `cv.md` English and `cv_es.md`
  Spanish; don't mechanically translate titles/degrees.
- **canonical-cv** — the two CV files are the single source of truth; keep them
  language-paired and consistent; read before editing.
- **project-structure** — the repo layout and output conventions above.
