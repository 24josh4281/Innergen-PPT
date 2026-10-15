# v28b 원본 반영 — 기존 PPT 갱신 · 고정 장표 자동 작성 (PC의 Slide Master 소스)

- `innergen_facts_update.py`: 기존 PPTX의 낡은 회사 값(숫자·연락처·브랜드 표기)을 원본 서식 그대로 고친 사본을 만든다.
- `innergen_standard_pages.py`: 회사소개서·이너캐리 소개서의 고정 장표(표지·회사 개요·사업 분야·핵심 숫자·맺음)를 원장 값으로 바로 그린다.
- 제목 검사(T02)가 "회사 개요"처럼 '요'로 끝나는 명사를 문장으로 보던 오탐을 고쳤다.

**v28을 먼저 반영해야 한다. v30(upstream-v30)은 앞뒤 어느 순서로 반영해도 된다.** 이 블록은 v30이 덮어쓰는 파일(SKILL.chat.md, innergen_qaqc.py)을 통째로 바꾸지 않고 필요한 줄만 넣는다. 두 번 실행해도 안전하다.
단, v30을 이 블록보다 **나중에** 반영했다면 이 블록을 한 번 더 실행한다(v30이 두 파일을 덮어쓰기 때문).

```powershell
$root = "B:\CODEX\Slide Master"
$src  = "$root\OUTPUTS\upstream-v28b"          # 이 폴더
if (-not (Test-Path "$root\.claude\skills\ppt-master\scripts\innergen_facts_check.py")) { throw "upstream-v28을 먼저 반영하세요" }
Set-Location $root
python "$src\apply_v28b_pc.py" $root
python .claude\skills\ppt-master\scripts\build_chat_skill.py
```

`apply_v28b_pc.py`가 하는 일:

- `innergen_facts_update.py`, `innergen_standard_pages.py` → `.claude\skills\ppt-master\scripts`
- `standard-decks-v28.md` → `docs\styles\innergen` (자동 작성 장 표 추가)
- `SKILL.chat.md`에 사용법 세 곳, `innergen_qaqc.py`·`qaqc-v21.json`에 제목 검사 예외, `build_chat_skill.py`의 `ENTRY_SCRIPTS`에 새 스크립트 두 개 추가(번들에 들어가게)

확인(선택):

```powershell
python .claude\skills\ppt-master\scripts\innergen_facts_update.py "<이너캐리 소개 자료 v4.1 경로>" --dry-run
```

`확인 필요라서 건너뛴 항목: 감축실적 인정량(만 톤), 브랜드 표기(INNerCarry)`와 `0 change(s)`가 나오면 정상이다(확인 필요 값은 기본으로 바꾸지 않는다).
