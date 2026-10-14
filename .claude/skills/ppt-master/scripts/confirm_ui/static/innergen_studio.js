/* Source-backed choices and illustrative layout previews. No acquisition happens here. */
(function (global) {
    "use strict";
    function node(tag, cls, text) {
        var n = document.createElement(tag); n.className = cls || "";
        if (text != null) n.textContent = text;
        return n;
    }
    function recommended(data, state) {
        if (data.consulting_structure) {
            return data.consulting_structure.goals[effectiveGoal(state)].layouts.slice();
        }
        var a = data.recommended_by_report[state.innergen_report_type] || ["evidence", "matrix", "process"];
        var b = data.recommended_by_business[state.innergen_business_type] || ["matrix"];
        return Array.from(new Set(a.slice(0, 2).concat(b, a))).slice(0, 3);
    }
    function effectiveGoal(state) {
        if (state.structure_goal && state.structure_goal !== "auto") return state.structure_goal;
        var mode = state.style_delivery_mode || "", report = state.innergen_report_type;
        if (mode.indexOf("education_") === 0) return "education";
        if (mode === "proposal" || report === "proposal") return "proposal";
        if (report === "interim") return "progress";
        if (state.innergen_business_type === "regulatory") return "requirements";
        if (report === "final") return "diagnosis";
        return "overview";
    }
    function contentMode(state) {
        var mode = state.style_delivery_mode || "";
        return mode.indexOf("education_") === 0 ? "education" :
            (["presentation", "proposal"].indexOf(mode) >= 0 ? mode : "report");
    }
    // Mode sizes plus the family's pinned roles (fixed template geometry), in px.
    function modePx(p, m, modeId) {
        var px = Object.assign({}, m.px), pinned = (p.typography_pt_overrides || {})[modeId] || {};
        Object.keys(pinned).forEach(function (role) { px[role] = pinned[role] / .75; });
        return px;
    }
    function apply(data, state, field, value) {
        state[field] = value;
        var p = data.profiles[state.style_family], m = data.modes[state.style_delivery_mode];
        if (!p || !m) return;
        state.design_standard_version = data.version;
        if (data.consulting_structure) state.structure_standard_version = data.consulting_structure.version;
        if (field === "style_family" || field === "style_delivery_mode") {
            state.canvas = p.canvas;
            state.visual_style = "custom";
            state.delivery_purpose = state.style_delivery_mode === "presentation" ? "presentation" : "text";
            state.color = { name: "v17-" + state.style_family, palette: {
                background: p.colors.background, secondary_bg: p.colors.panel,
                primary: p.colors.primary, accent: p.colors.accent,
                secondary_accent: p.colors.muted, body_text: p.colors.text
            }};
            var px = modePx(p, m, state.style_delivery_mode);
            state.typography = { name: "v17-" + state.style_family,
                heading: { cjk: p.font, latin: p.font }, body: { cjk: p.font, latin: p.font },
                body_size: px.body, body_size_unit: "px",
                sizes: Object.assign({}, px, { subtitle: px.governing, annotation: px.note }) };
        }
        if (field === "media_mode") state.image_usage = data.media_modes[value].image_usage.slice();
        if (!state.layout_choice || field === "structure_goal" || field === "innergen_report_type" ||
                field === "innergen_business_type" || field === "style_delivery_mode") {
            state.layout_choice = recommended(data, state)[0];
        }
    }
    function select(root, label, entries, value, change, disabled) {
        var wrap = node("label", "ig-field"), input = node("select");
        wrap.appendChild(node("span", "", label)); input.setAttribute("aria-label", label);
        Object.keys(entries).forEach(function (id) {
            var item = entries[id], opt = node("option", "", item.label || item.label_ko || id);
            opt.value = id; input.appendChild(opt);
        });
        input.value = value; input.disabled = !!disabled;
        input.addEventListener("change", function () { change(input.value); });
        wrap.appendChild(input); root.appendChild(wrap);
    }
    function table(headers, rows) {
        var wrap = node("div", "ig-table-wrap"), t = node("table", "ig-rich-table");
        var head = node("thead"), tr = node("tr");
        headers.forEach(function (label) { var th = node("th", "", label); th.scope = "col"; tr.appendChild(th); });
        head.appendChild(tr); t.appendChild(head);
        var body = node("tbody");
        rows.forEach(function (row) {
            var line = node("tr");
            headers.forEach(function (_, index) { line.appendChild(node("td", "", row[index] == null ? "확인 필요" : row[index])); });
            body.appendChild(line);
        });
        t.appendChild(body); wrap.appendChild(t); return wrap;
    }
    function panel(title, text, cls) {
        var p = node("div", "ig-rich-panel " + (cls || ""));
        p.appendChild(node("strong", "", title));
        if (text) p.appendChild(node("p", "", text));
        return p;
    }
    function branches(example, outputs) {
        var tree = node("div", "ig-tree"), row = node("div", "ig-tree-children");
        tree.appendChild(node("div", "ig-tree-parent", example.parent));
        example.children.forEach(function (label, i) {
            row.appendChild(panel(label, outputs ? outputs[i] : "", "ig-tree-child"));
        });
        tree.appendChild(row); return tree;
    }
    function richBody(body, layout, education) {
        var ex = layout.preview, kind = layout.pattern;
        body.className = "ig-rich-body ig-rich-" + kind;
        if (kind === "concept") {
            body.appendChild(branches(ex)); body.appendChild(table(ex.headers, ex.rows));
        } else if (kind === "tree") {
            body.appendChild(branches(ex, ex.outputs));
            body.appendChild(node("p", "ig-relation-note", "선 = 과업의 포함 관계 · 업무 순서를 뜻하지 않음"));
        } else if (kind === "qa") {
            body.appendChild(panel("사례", ex.case, "ig-case"));
            body.appendChild(panel("질문", ex.question));
            var answers = node("div", "ig-answer-pair");
            answers.appendChild(panel("정답", ex.answer)); answers.appendChild(panel("이유", ex.reason)); body.appendChild(answers);
        } else if (kind === "asymmetric") {
            var cols = node("div", "ig-asymmetric-cols"), left = node("section"), right = node("section");
            left.appendChild(node("h3", "ig-band", ex.left_title));
            left.appendChild(table(["항목", "확인 내용"], ex.left_rows));
            right.appendChild(node("h3", "ig-band", ex.right_title)); right.appendChild(panel("독립 요구", ex.right_body));
            cols.appendChild(left); cols.appendChild(right); body.appendChild(cols);
            body.appendChild(node("div", "ig-integration", ex.integration));
        } else if (kind === "process_fields") {
            var steps = node("div", "ig-process-steps");
            ex.steps.forEach(function (step, i) {
                var box = node("div", "ig-process-step");
                box.appendChild(node("h3", "ig-band", String(i + 1).padStart(2, "0") + " " + step.name));
                [["입력", step.input], ["수행", step.action], ["산출", step.output]].forEach(function (row) {
                    box.appendChild(panel(row[0], row[1]));
                });
                steps.appendChild(box);
            }); body.appendChild(steps);
            body.appendChild(node("p", "ig-relation-note", "→ 앞 단계의 산출물이 다음 단계의 입력이 되는 순서 예시"));
        } else if (kind === "decision") {
            body.appendChild(node("div", "ig-decision-question", ex.question));
            var choices = node("div", "ig-decision-branches");
            [ex.yes, ex.no, ex.unknown].forEach(function (text) {
                var parts = text.split(" · "); choices.appendChild(panel(parts[0], parts.slice(1).join(" · ")));
            }); body.appendChild(choices);
        } else if (kind === "chart" || kind === "chart_table") {
            var area = node("div", "ig-chart-pair"), chart = node("div", "ig-bar-chart");
            var max = Math.max.apply(null, ex.bars.map(function (b) { return b[1]; }));
            ex.bars.forEach(function (item) {
                var row = node("div", "ig-bar-row"); row.appendChild(node("span", "", item[0]));
                var track = node("div", "ig-bar-track"), bar = node("span", "ig-bar");
                bar.style.width = item[1] / max * 100 + "%"; track.appendChild(bar); row.appendChild(track);
                row.appendChild(node("strong", "", item[1])); chart.appendChild(row);
            });
            chart.appendChild(node("p", "ig-relation-note", "0 기준 · " + ex.unit)); area.appendChild(chart);
            area.appendChild(kind === "chart_table" ? table(ex.headers, ex.rows) : panel("해석과 한계", ex.insight));
            body.appendChild(area);
        } else {
            body.appendChild(table(ex.headers, ex.rows));
        }
        if (ex.condition) body.appendChild(node("div", "ig-condition", ex.condition));
        if (education && layout.education_detail) {
            var detail = node("div", "ig-education-detail");
            layout.education_detail.forEach(function (row) { detail.appendChild(panel(row[0], row[1])); });
            body.appendChild(detail);
        }
    }
    function mini(layout) {
        var kind = layout.pattern, ex = layout.preview || {}, root = node("div", "ig-mini ig-mini-" + kind);
        root.setAttribute("aria-hidden", "true");
        var labels = ex.children || ex.headers || (ex.steps && ex.steps.map(function (s) { return s.name; })) || layout.slots;
        if (kind === "qa") labels = ["사례", "질문", "정답·이유"];
        if (kind === "asymmetric") labels = ["대상 A 상세", "대상 B", "공통 통합·조건"];
        if (kind === "decision") labels = ["판단 조건", "예", "아니오", "미확인"];
        if (kind === "chart" || kind === "chart_table") labels = ["값 비교", "지표·해석", "단위·출처"];
        labels.slice(0, 5).forEach(function (text) { root.appendChild(node("span", "", text)); });
        return root;
    }
    function preview(root, data, state, compact) {
        var profile = data.profiles[state.style_family], layout = data.layouts[state.layout_choice];
        var stage = data.report_types[state.innergen_report_type], business = data.business_types[state.innergen_business_type];
        var slide = node("div", "ig-slide ig-" + state.style_family + (compact ? " ig-compact" : ""));
        var palette = state.color && state.color.palette || {};
        slide.style.setProperty("--ig-ink", palette.body_text || profile.colors.text);
        slide.style.setProperty("--ig-primary", palette.primary || profile.colors.primary);
        slide.style.setProperty("--ig-accent", palette.accent || profile.colors.accent);
        slide.style.setProperty("--ig-panel", palette.secondary_bg || profile.colors.panel);
        slide.style.setProperty("--ig-border", profile.colors.border);
        var family = state.typography && state.typography.body && state.typography.body.cjk || profile.font;
        slide.style.fontFamily = '"' + family + '", "Malgun Gothic", sans-serif';
        var mode = data.modes[state.style_delivery_mode], ty = state.typography || {}, sizes = ty.sizes || {};
        slide.style.setProperty("--ig-ratio", profile.canvas_pt[0] + " / " + profile.canvas_pt[1]);
        slide.style.setProperty("--ig-title-size", (sizes.title == null ? mode.pt.title : Number(sizes.title) * .75) + "px");
        slide.style.setProperty("--ig-body-size", (ty.body_size == null ? mode.pt.body : Number(ty.body_size) * .75) + "px");
        slide.style.setProperty("--ig-table-size", (sizes.table == null ? mode.pt.table : Number(sizes.table) * .75) + "px");
        slide.style.setProperty("--ig-claim-size", (sizes.governing == null ? mode.pt.governing : Number(sizes.governing) * .75) + "px");
        slide.appendChild(node("div", "ig-slide-label", profile.label + " · " + mode.label + " · 구성 예시"));
        slide.appendChild(node("div", "ig-slide-title", layout.preview ? layout.preview.title : business.label_ko + " | " + layout.label));
        slide.appendChild(node("div", "ig-claim", layout.preview ? layout.preview.claim : (stage.must_have || ["핵심 판단과 근거"])[0]));
        var body = node("div", "ig-layout ig-pattern-" + layout.pattern);
        if (layout.preview) {
            slide.classList.add("ig-rich-slide");
            richBody(body, layout, contentMode(state) === "education");
        } else if (layout.pattern === "table") {
            var table = node("table"), head = node("thead"), tr = node("tr");
            layout.slots.forEach(function (s) { tr.appendChild(node("th", "", s)); }); head.appendChild(tr); table.appendChild(head);
            var tbody = node("tbody");
            (business.required || []).slice(0, 3).forEach(function (s, i) {
                var row = node("tr"); layout.slots.forEach(function (_, col) {
                    row.appendChild(node("td", "", col === 0 ? s : "예시 · 자료 확인"));
                }); tbody.appendChild(row);
            }); table.appendChild(tbody); body.appendChild(table);
        } else {
            layout.slots.forEach(function (s, i) {
                var block = node("div", "ig-block");
                if (["flow", "timeline"].indexOf(layout.pattern) >= 0) block.appendChild(node("div", "ig-step", String(i + 1).padStart(2, "0")));
                block.appendChild(node("strong", "", s));
                block.appendChild(node("span", "", (business.required || [])[i] || "현재 자료로 확인"));
                if (layout.pattern === "screen" && i === 0) block.appendChild(node("small", "", "삽입 전 예시 영역 · 실제 제품 화면 아님"));
                body.appendChild(block);
            });
        }
        slide.appendChild(body);
        slide.appendChild(node("div", "ig-slide-footer", "가상 구성 예시 · 실제 자료로 교체 · 도식의 뜻과 관계를 비교하는 화면"));
        root.appendChild(slide);
        return slide;
    }
    function mount(host, options) {
        var data = options.data, state = options.state, onChange = options.onChange;
        var root = node("section", "ig-studio"); root.setAttribute("aria-label", "이너젠 간편 선택");
        root.appendChild(node("h2", "", "목적을 고르면, 맞는 구조 3개를 보여드립니다"));
        var choices = node("div", "ig-design-choices");
        Object.keys(data.profiles).forEach(function (id) {
            var p = data.profiles[id], button = node("button", "ig-design", p.label);
            button.type = "button"; button.dataset.profile = id;
            button.setAttribute("aria-pressed", String(state.style_family === id));
            button.disabled = !!options.locked;
            var stripe = node("span", "ig-stripe"); stripe.style.background = p.colors.primary;
            button.prepend(stripe); button.appendChild(node("small", "", p.canvas_pt.join(" × ") + " pt · " + p.font));
            button.addEventListener("click", function () { onChange("style_family", id); }); choices.appendChild(button);
        }); root.appendChild(choices);
        if (options.locked) root.appendChild(node("p", "ig-caption", "설치된 템플릿의 화면·글꼴은 유지합니다. 변경은 상세 설정에서 확인하세요."));
        var fields = node("div", "ig-fields");
        select(fields, "사업 성격", data.business_types, state.innergen_business_type, function (v) { onChange("innergen_business_type", v); });
        select(fields, "보고 성격", data.report_types, state.innergen_report_type, function (v) { onChange("innergen_report_type", v); });
        select(fields, "사용 방식", data.modes, state.style_delivery_mode, function (v) { onChange("style_delivery_mode", v); }, options.locked);
        root.appendChild(fields);
        var catalog = data.consulting_structure;
        if (catalog) {
            var modeContract = catalog.mode_contracts[contentMode(state)];
            var modeInfo = node("div", "ig-mode-contract");
            modeInfo.appendChild(node("strong", "", modeContract.label + " · " + modeContract.question));
            modeInfo.appendChild(node("p", "", modeContract.modules.join(" → ")));
            modeInfo.appendChild(node("small", "", "자료 구성의 읽기 순서입니다. 실제 업무 절차를 뜻하지 않습니다.")); root.appendChild(modeInfo);
            var otherGoal = node("details", "ig-other-goal");
            otherGoal.appendChild(node("summary", "", "다른 질문으로 추천받기 · 현재: " + catalog.goals[effectiveGoal(state)].label));
            select(otherGoal, "이번 장표의 질문", catalog.goals, state.structure_goal || "auto", function (v) { onChange("structure_goal", v); });
            root.appendChild(otherGoal);
        }
        var recs = recommended(data, state), available = state.studio_show_all ? Object.keys(data.layouts) : recs;
        if (available.indexOf(state.layout_choice) < 0) available.push(state.layout_choice);
        if (state.studio_show_all) {
            var search = node("input", "ig-search"); search.type = "search";
            search.placeholder = "구조 이름·설명으로 찾기"; search.setAttribute("aria-label", "구조 검색");
            search.value = state.studio_query || "";
            search.addEventListener("input", function () {
                var q = search.value.trim().toLowerCase(); state.studio_query = search.value;
                root.querySelectorAll(".ig-structure").forEach(function (card) { card.hidden = card.textContent.toLowerCase().indexOf(q) < 0; });
            }); root.appendChild(search);
        }
        var layoutrow = node("div", "ig-structure-choices");
        available.forEach(function (id) {
            var item = data.layouts[id], b = node("button", "ig-structure", item.label);
            b.type = "button"; b.dataset.layout = id; b.setAttribute("aria-pressed", String(state.layout_choice === id));
            b.prepend(mini(item));
            if (recs.indexOf(id) >= 0) b.appendChild(node("span", "ig-rec-badge", "추천 " + (recs.indexOf(id) + 1)));
            b.appendChild(node("small", "", item.purpose));
            if (state.studio_show_all && state.studio_query) b.hidden = b.textContent.toLowerCase().indexOf(state.studio_query.toLowerCase()) < 0;
            b.addEventListener("click", function () { onChange("layout_choice", id); }); layoutrow.appendChild(b);
        }); root.appendChild(layoutrow);
        var all = node("button", "ig-all", state.studio_show_all ? "추천 구조만 보기" : "전체 구조 " + Object.keys(data.layouts).length + "개 보기");
        all.type = "button"; all.addEventListener("click", function () { onChange("studio_show_all", !state.studio_show_all); }); root.appendChild(all);
        var display = node("div", "ig-preview"); display.setAttribute("aria-live", "polite"); preview(display, data, state); root.appendChild(display);
        var chosen = data.layouts[state.layout_choice];
        if (chosen.required_evidence) {
            var contract = node("div", "ig-choice-contract");
            contract.appendChild(node("strong", "", "이 구조에 필요한 자료"));
            contract.appendChild(node("p", "", chosen.required_evidence.join(" · ")));
            contract.appendChild(node("strong", "", "작성할 때 유지할 것"));
            contract.appendChild(node("p", "", chosen.protect.join(" · "))); root.appendChild(contract);
        }
        var p = data.profiles[state.style_family], m = data.modes[state.style_delivery_mode];
        var typ = state.typography || {}, sizes = typ.sizes || {};
        function pt(value, fallback) { return value == null ? fallback : Math.round(Number(value) * .75 * 100) / 100; }
        root.appendChild(node("p", "ig-metrics", (typ.body && typ.body.cjk || p.font) + " · 제목 " + pt(sizes.title, m.pt.title) + "pt · 핵심 문장 " + pt(sizes.governing, m.pt.governing) + "pt · 본문 " + pt(typ.body_size, m.pt.body) + "pt · 표 " + pt(sizes.table, m.pt.table) + "pt · 열 간격 12pt"));
        select(root, "도식·그림 사용", data.media_modes, state.media_mode, function (v) { onChange("media_mode", v); });
        root.appendChild(node("p", "ig-caption", data.media_modes[state.media_mode].description + " · 검색·생성은 장표 제작 단계에서 실행합니다."));
        if (state.innergen_report_type === "interim") root.appendChild(node("p", "ig-caption", "중간보고는 구성 제안입니다. 직접 해당하는 원본으로 확인된 자료는 없습니다."));
        root.appendChild(node("p", "ig-caption", "미리보기는 구조 예시이며 PPT 출력 검증을 대신하지 않습니다. 상세 설정의 변경값이 제작에 우선합니다."));
        host.appendChild(root); return root;
    }
    global.InnergenStudio = { mount: mount, apply: apply, recommended: recommended, preview: preview,
        effectiveGoal: effectiveGoal, contentMode: contentMode };
}(window));
