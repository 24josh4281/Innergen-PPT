# Python runtime and file delivery

## 1. Resolve the actual environment

Use a Python execution tool or shell provided by the host. Run
`scripts/environment_check.py` with its Python interpreter before generation.
It reports required libraries, fonts and available renderers without installing
anything. A ZIP attachment alone does not enable code execution.

| Host | Working files and command execution |
|---|---|
| ChatGPT Python tool | Use a new folder under `/mnt/data`; run scripts with `subprocess.run([sys.executable, script, ...], capture_output=True, text=True, encoding="utf-8")`. Inspect both output streams and return code. |
| Work cloud | Resolve the installed skill path and use the host's writable workspace/output directory. Do not assume `/mnt/data` or a particular tool name. |
| Work local | Use the task workspace and its configured Python, preferably its existing virtual environment. Preserve originals and user-selected output paths. |

In the detailed deck workflow, `/tmp/<deck>` means the chosen project directory;
`/mnt/user-data/outputs/<title>.pptx` means the host's downloadable output path;
`${SKILL_DIR}` always means the installed skill root, not `references/`.

If a dependency is missing, report its exact name. Install only when the host
supports it and the task authorization permits it. If code execution or required
dependencies are unavailable, stop file generation and state what is missing.
Do not pretend a skill is installed or create a substitute bitmap deck.

## 2. Preserve versions and inspect the output

Create new project/output names (`_v1`, `_v2`) instead of deleting or forcing a
scaffold over an existing project. Back up an SVG before using a checker with
`--fix`. Keep the installed skill read-only; copy its templates into the project.

The deck skill uses `python-pptx`, `lxml`, `Pillow`, `openpyxl`, `XlsxWriter` and
`PyYAML`; the equations skill requires `python-pptx`. Requirements files describe
these libraries without assuming internet access. Do not call external APIs or
use API keys as an automatic fallback.

If a host denies access to its default temporary folder, set `TEMP`, `TMP` and
`TMPDIR` only in the child process environment to a new temporary directory
inside the writable task workspace. Keep that change local to this task.

Font availability depends on the host. Preserve the family's Pretendard or IBM
Plex Sans KR names. Inspect actual fonts when rendering; disclose fallback and
the need for the opening PC to have the intended fonts. Fonts are not embedded.

If LibreOffice exists, export a PDF and view page images. If using the full
repository on Windows, follow its safe PowerPoint renderer rules. Do not run
OfficeCLI native rendering, which may close the user's PowerPoint decks.
If no renderer exists, complete structural checks and report rendering unverified.

## 3. Return files through the host

Use the host's file attachment or artifact delivery mechanism. In a ChatGPT
Python sandbox, use `sandbox:/mnt/data/<path>` links to generated files. In a
local Work task, use absolute local file links. Do not emit sandbox links to
files that only exist on the local computer.

When a sandbox resets, recover from the uploaded package and saved project
artifacts. If the ZIP is inaccessible, ask the user to attach it to the current
chat. Never select an unrelated ZIP based only on alphabetical order.
