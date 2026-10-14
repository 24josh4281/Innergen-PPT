# GEMINI.md — Gemini CLI execution rules for slide-master

This repo is **multi-host**: Claude Code, Codex (GPT) and Gemini CLI share one
skill set. [`CLAUDE.md`](CLAUDE.md) owns standing repository conventions and
[`AGENTS.md`](AGENTS.md) owns the agent-side enforcement rules; both are imported
below and apply to Gemini CLI unchanged except for the substitutions in this file.
Route selection belongs to
[`.claude/skills/ppt-master/workflows/routing.md`](.claude/skills/ppt-master/workflows/routing.md).

## Gemini CLI substitutions

- **Skill source.** `.claude/skills/` is canonical. `.gemini/skills/` holds
  **generated** discovery stubs (same `name`/`description` plus a redirect body
  and Gemini adaptation notes). Read the rules in `AGENTS.md` about
  `.codex/skills/` as applying equally to `.gemini/skills/`: never hand-edit
  them; edit the `.claude` tree, then run
  `python3 .claude/skills/ppt-master/scripts/sync_codex_stubs.py`, which
  regenerates both stub sets. `preflight.py` fails while either is stale.
- **Activation.** When a stub is activated, its body tells you which canonical
  file to read next. Canonical files live in this workspace, so read them
  directly; the stub directory is not where `references/`, `workflows/`,
  `scripts/` or `templates/` are.
- **Tools.** Canonical text names Claude Code tools. Use the Gemini CLI
  equivalent (file read/write/replace, `run_shell_command`, glob/search, web
  fetch/search). An AskUserQuestion or other blocking confirmation becomes the
  same question in chat; end the turn and wait. Work described as delegated to
  a subagent is done by you, serially, in this session.
- **Images.** Gemini CLI has no built-in image tool. Where `AGENTS.md` says the
  default `codex` path uses Codex built-in `image_gen`, run
  `.claude/skills/ppt-master/scripts/image_gen.py` instead: the default `codex`
  backend works when the Codex CLI is installed and logged in; otherwise use
  `IMAGE_BACKEND=gemini` with `GEMINI_API_KEY` in `.env`. Retry, `Needs-Manual`
  and no-substitution rules are unchanged.
- **Python.** Run repository scripts with the `.venv` interpreter when it exists
  (`.venv\Scripts\python.exe` on Windows, `.venv/bin/python` elsewhere). Create
  it with `setup.ps1` / `setup.sh`.

Every confirmation, validation, export and completion gate of the selected owner
applies to Gemini CLI exactly as written.

## Imported rules

@./CLAUDE.md

@./AGENTS.md
