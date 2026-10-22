#!/usr/bin/env node
'use strict';

// PreToolUse guard: block `officecli view <file> screenshot|pdf` unless it
// passes `--render html`. OfficeCLI's default native render drives PowerPoint
// and quits it afterwards; a deck the user has open, or opens while the render
// runs, joins that instance and closes without saving.
// Opt-in for a PowerPoint-exact render: SLIDE_MASTER_NATIVE_RENDER=1 in the
// command (after the user saved and closed every PowerPoint window).

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { raw += chunk; });
process.stdin.on('end', () => {
  let command = '';
  try {
    command = String((JSON.parse(raw).tool_input || {}).command || '');
  } catch (err) {
    process.exit(0);
  }
  if (findUnsafeRender(command)) {
    process.stderr.write(
      'Blocked: officecli view screenshot/pdf without `--render html`. The native '
      + 'render quits PowerPoint and closes the user\'s open decks unsaved. For '
      + 'PowerPoint-exact wraps use .claude/skills/ppt-master/scripts/'
      + 'pptx_safe_render.py (leaves PowerPoint open); otherwise add '
      + '`--render html`.\n');
    process.exit(2);
  }
  process.exit(0);
});

function findUnsafeRender(command) {
  if (/SLIDE_MASTER_NATIVE_RENDER\s*=\s*["']?1/.test(command)) return false;
  // One shell statement at a time, so a later `--render html` cannot cover an
  // earlier call.
  const joined = command.replace(/[\\`]\r?\n/g, ' ');
  return joined.split(/&&|\|\||[;\n|]/).some((statement) => {
    if (!/\bofficecli(?:\.cmd|\.exe)?["']?\s/i.test(statement)) return false;
    if (!/\bview\b/i.test(statement)) return false;
    if (!/\b(?:screenshot|pdf)\b/i.test(statement)) return false;
    return !/--render(?:\s+|=)["']?html\b/i.test(statement);
  });
}
