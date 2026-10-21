# Claude 채팅 · Claude Cowork · Codex 적용 방법

| 사용처 | 적용 방법 |
|---|---|
| Claude Code (이 저장소) | 자동 적용. `.claude/skills/ppt-content-group-centering/`에 있고 `content_balance_check.py`가 `verify_deck.py`에서 실행된다 |
| Codex (이 저장소) | 자동 적용. `.codex/skills/` 안내 파일이 이 스킬을 가리킨다(`sync_codex_stubs.py`로 생성) |
| Claude 채팅 (claude.ai) | 설정 → Capabilities → Skills → 스킬 업로드에 `ppt-content-group-centering.zip`을 올린다 |
| Claude Cowork | Customize → Skills에서 같은 ZIP을 올리고 켠다 |
| ChatGPT 채팅 · Work | `CHATGPT_INSTRUCTIONS.md`의 구분선 안쪽을 프로젝트 지침에 붙여 넣는다 |
| 다른 PC의 Codex (저장소 없이) | ZIP을 풀어 `~/.codex/skills/ppt-content-group-centering/`에 둔다 |

ZIP은 저장소 `OUTPUTS/ppt-content-group-centering.zip`에 있다. 스킬 내용이 바뀌면 다시 만든다.

```bash
python .claude/skills/ppt-content-group-centering/scripts/build_skill_zip.py
```

ZIP에는 SVG 검사기(`content_balance_check.py`)도 들어 있다. 채팅 환경에서도 같은 검사로 확인할 수 있다.

## Claude 채팅 지침으로만 쓸 때 (스킬 업로드가 안 될 때)

프로젝트 지침에 `CHATGPT_INSTRUCTIONS.md`의 구분선 안쪽을 그대로 붙여 넣는다. 내용은 공통이다.
