---
template_id: innergen
deck_id: innergen
kind: deck
category: brand
summary: 이너젠 오리지널 (ESG·기후 컨설팅 보고서 13:9) 템플릿 — 격자형·단색 남색형·슬림라인형
keywords: [이너젠, 이너젠 오리지널, 오리지널, ESG, 기후, 보고서, '13:9']
primary_color: "#0F243F"
canvas_format: ppt139
canvas_width: 1040
canvas_height: 720
canvas_viewbox: "0 0 1040 720"
source_canvas_width: 1040
source_canvas_height: 720
source_viewbox: "0 0 1040 720"
replication_mode: standard
native_structure_mode: structured
page_count: 21
---

# 이너젠 오리지널 (컨설팅 보고서 13:9) 템플릿 — 디자인 명세

## I. Template Overview

이너젠의 자체 로고와 남색·흰색·회색 구조색을 사용하는 ESG·기후 컨설팅 보고서용 덱 템플릿이다. 원본 PPTX에서 관찰된 `classic-grid`, `solid-navy`, `slim-line` 세 프레임을 각각 독립된 화면 계열로 제공한다. 한 덱에서는 선택한 프레임을 일관되게 사용한다. 사업 성격과 보고 성격은 별도 구성 프로필에서 정하며, 이 템플릿은 재사용할 화면 형식을 제공한다.

## II. Color Scheme

| 역할 | HEX | 적용 |
| --- | --- | --- |
| 구조 남색 | `#0F243F` | 헤더·푸터·밑줄 |
| 본문 배경 | `#FFFFFF` | 표지와 본문 바탕 |
| 기본 글자 | `#000000` | 본문·슬림라인 제목 |
| 자료 제목 | `#808080` | 자료 프레임 제목 띠 |
| 보조 면 | `#F2F2F2` | 표·목차·보조 구획 |
| 경계선 | `#BFBFBF` | 표와 자료 프레임 |
| 의미 강조 | `#FF0000` | 실제 위험·차이·보완 필요 항목에만 사용 |

## III. Typography

- 기본형은 Malgun Gothic, 단색 남색형과 슬림라인형은 IBM Plex Sans KR를 우선한다. 이는 각 대표 원본의 본문 서체 관측에 따른다.
- 다른 장치에 IBM Plex Sans KR가 없으면 Malgun Gothic으로 대체하고 글자 폭·줄바꿈을 다시 확인한다. 프로젝트에서 확인한 글자 크기가 이 템플릿의 예시 크기보다 우선한다.
- 템플릿의 텍스트는 모두 편집 가능한 SVG 텍스트로 저작한다.

## IV. Signature Design Elements

- `classic-grid`: 낮은 대비의 미세 격자를 남색 헤더와 푸터에만 두고, 헤더 오른쪽을 대각선으로 마무리한다. 본문은 흰색이며 자료 블록에 회색 제목 띠를 사용할 수 있다.
- `solid-navy`: 격자 없는 남색 헤더와 단순한 남색 푸터를 쓴다. 내용 안에는 목적에 맞는 표·도식·근거 화면을 배치한다.
- `slim-line`: 흰 헤더의 검은 제목 아래 가는 남색 구분선을 놓는다. 흰 푸터 왼쪽에 자체 로고, 중앙에 페이지 번호를 둔다.
- 표지에는 파란 자체 로고, 남색 바탕에는 흰 자체 로고를 원본 비율 그대로 사용한다. 고객사·협력사 로고를 템플릿에 고정하지 않는다.
- 본문은 제목 아래 핵심 설명을 먼저 읽고, 그 아래에 표·비교·절차·차트를 배치할 수 있는 넓은 영역을 남긴다. 차트 색과 숫자·단위는 현재 프로젝트 자료에 따라 결정한다.

## V. Page Roster

모든 원형은 새 Master `innergen-master-13x9`를 사용한다. 각 Layout은 파일별로 고유하며, 아래 세 프레임을 한 페이지 안에서 혼합하지 않는다.

| SVG | Layout key / picker | 화면 성격 |
| --- | --- | --- |
| `01a_cover_classic.svg` | `innergen-classic-cover` / 이너젠 오리지널 격자 표지 | 가운데 제목·자체 로고·남색 하단 띠 |
| `01b_cover_solid_navy.svg` | `innergen-solid-cover` / 이너젠 오리지널 단색 표지 | 왼쪽 제목·절제된 남색 구조·자체 로고 |
| `01c_cover_slim_line.svg` | `innergen-slim-cover` / 이너젠 오리지널 슬림 표지 | 흰 바탕·가느다란 상단 선·간결한 제목 |
| `02a_toc_classic.svg` | `innergen-classic-toc` / 이너젠 오리지널 격자 목차 | 격자 헤더·번호별 목차 |
| `02a_toc_classic_4.svg` | `innergen-classic-toc-4` / 이너젠 오리지널 격자 목차 4장 | 격자 헤더·번호별 목차·4장 |
| `02a_toc_classic_5.svg` | `innergen-classic-toc-5` / 이너젠 오리지널 격자 목차 5장 | 격자 헤더·번호별 목차·5장 |
| `02b_toc_solid_navy.svg` | `innergen-solid-toc` / 이너젠 오리지널 단색 목차 | 단색 헤더·번호별 목차 |
| `02b_toc_solid_navy_4.svg` | `innergen-solid-toc-4` / 이너젠 오리지널 단색 목차 4장 | 단색 헤더·번호별 목차·4장 |
| `02b_toc_solid_navy_5.svg` | `innergen-solid-toc-5` / 이너젠 오리지널 단색 목차 5장 | 단색 헤더·번호별 목차·5장 |
| `02c_toc_slim_line.svg` | `innergen-slim-toc` / 이너젠 오리지널 슬림 목차 | 얇은 남색 구분선·번호별 목차 |
| `02c_toc_slim_line_4.svg` | `innergen-slim-toc-4` / 이너젠 오리지널 슬림 목차 4장 | 얇은 남색 구분선·번호별 목차·4장 |
| `02c_toc_slim_line_5.svg` | `innergen-slim-toc-5` / 이너젠 오리지널 슬림 목차 5장 | 얇은 남색 구분선·번호별 목차·5장 |
| `03a_chapter_classic.svg` | `innergen-classic-chapter` / 이너젠 오리지널 격자 장 구분 | 현재 장을 굵게 표시하는 장 구분 |
| `03b_chapter_solid_navy.svg` | `innergen-solid-chapter` / 이너젠 오리지널 단색 장 구분 | 단색 남색 제목띠의 장 구분 |
| `03c_chapter_slim_line.svg` | `innergen-slim-chapter` / 이너젠 오리지널 슬림 장 구분 | 흰 화면과 남색 선의 장 구분 |
| `04a_content_classic.svg` | `innergen-classic-content` / 이너젠 오리지널 격자 본문 | 핵심 설명·자료 프레임·출처 |
| `04b_content_solid_navy.svg` | `innergen-solid-content` / 이너젠 오리지널 단색 본문 | 핵심 설명·넓은 자료 영역·출처 |
| `04c_content_slim_line.svg` | `innergen-slim-content` / 이너젠 오리지널 슬림 본문 | 얇은 선 아래 핵심 설명·넓은 자료 영역 |
| `05a_ending_classic.svg` | `innergen-classic-ending` / 이너젠 오리지널 격자 마무리 | 핵심 결론·자체 로고·남색 하단 띠 |
| `05b_ending_solid_navy.svg` | `innergen-solid-ending` / 이너젠 오리지널 단색 마무리 | 핵심 결론·단색 남색 하단 띠 |
| `05c_ending_slim_line.svg` | `innergen-slim-ending` / 이너젠 오리지널 슬림 마무리 | 흰 여백·짧은 종료 메시지·가는 구분선 |

## VI. Assets

| 파일 | 용도 |
| --- | --- |
| `../images/innergen-logo-cover-blue.png` | 흰 표지·슬림라인 푸터, 709×709 원본 |
| `../images/innergen-logo-footer-white.png` | 남색 푸터, 160×101 원본 |

두 파일 모두 이너젠 원본에서 확인한 자체 로고이다. 과거 고객 로고·연락처·수치·일러스트는 포함하지 않는다.
