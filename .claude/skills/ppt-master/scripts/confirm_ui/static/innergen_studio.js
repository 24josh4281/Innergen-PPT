/* Source-backed choices and illustrative layout previews. No acquisition happens here. */
(function (global) {
    "use strict";
    function node(tag, cls, text) {
        var n = document.createElement(tag); n.className = cls || "";
        if (text != null) n.textContent = text;
        return n;
    }
    function recommended(data, state) {
        var a = data.recommended_by_report[state.innergen_report_type] || ["evidence", "matrix", "process"];
        var b = data.recommended_by_business[state.innergen_business_type] || ["matrix"];
        return Array.from(new Set(a.slice(0, 2).concat(b, a))).slice(0, 3);
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
        if (!state.layout_choice || field === "innergen_report_type" || field === "innergen_business_type") {
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
        slide.appendChild(node("div", "ig-slide-label", profile.label + " · " + (stage.label_ko || "") + " · 구성 예시"));
        slide.appendChild(node("div", "ig-slide-title", business.label_ko + " | " + layout.label));
        slide.appendChild(node("div", "ig-claim", (stage.must_have || ["핵심 판단과 근거"])[0]));
        var body = node("div", "ig-layout ig-pattern-" + layout.pattern);
        if (layout.pattern === "table") {
            var table = node("table"), head = node("thead"), tr = node("tr");
            layout.slots.forEach(function (s) { tr.appendChild(node("th", "", s)); }); head.appendChild(tr); table.appendChild(head);
            var tbody = node("tbody");
            (business.required || []).slice(0, 3).forEach(function (s, i) {
                var row = node("tr"); [s, ["확인 완료", "자료 확인 중", "보완 필요"][i], ["근거 연결", "담당 확인", "기한 협의"][i]].forEach(function (v) { row.appendChild(node("td", "", v)); }); tbody.appendChild(row);
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
        slide.appendChild(node("div", "ig-slide-footer", "예시 문구·상태 · 실제 프로젝트 자료로 교체"));
        root.appendChild(slide);
        return slide;
    }
    function mount(host, options) {
        var data = options.data, state = options.state, onChange = options.onChange;
        var root = node("section", "ig-studio"); root.setAttribute("aria-label", "이너젠 간편 선택");
        root.appendChild(node("h2", "", "디자인과 보고 목적부터 선택하세요"));
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
        var recs = recommended(data, state), available = state.studio_show_all ? Object.keys(data.layouts) : recs;
        if (available.indexOf(state.layout_choice) < 0) available.push(state.layout_choice);
        var layoutrow = node("div", "ig-structure-choices");
        available.forEach(function (id) {
            var item = data.layouts[id], b = node("button", "ig-structure", item.label);
            b.type = "button"; b.dataset.layout = id; b.setAttribute("aria-pressed", String(state.layout_choice === id));
            b.appendChild(node("small", "", item.purpose));
            b.addEventListener("click", function () { onChange("layout_choice", id); }); layoutrow.appendChild(b);
        }); root.appendChild(layoutrow);
        var all = node("button", "ig-all", state.studio_show_all ? "추천 구조만 보기" : "전체 구조 " + Object.keys(data.layouts).length + "개 보기");
        all.type = "button"; all.addEventListener("click", function () { onChange("studio_show_all", !state.studio_show_all); }); root.appendChild(all);
        var display = node("div", "ig-preview"); display.setAttribute("aria-live", "polite"); preview(display, data, state); root.appendChild(display);
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
    global.InnergenStudio = { mount: mount, apply: apply, recommended: recommended, preview: preview };
}(window));
