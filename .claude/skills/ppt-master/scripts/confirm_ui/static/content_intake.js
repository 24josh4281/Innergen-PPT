/* PPT Master - Optional file-first intake and complete outline review. */
(function () {
    "use strict";
    var savedState = null, activeInfo = null, activeLang = "en";
    var pending = 0, pollTimer = null, uploadQueue = Promise.resolve(), redraw = [];
    var MAX_BYTES = 100 * 1024 * 1024;
    var ACCEPT = ".pptx,.ppt,.pdf,.docx,.doc,.xlsx,.xls,.xlsm,.csv,.tsv,.txt,.md,.json,.png,.jpg,.jpeg,.webp";
    var WORDS = {
        ko: {
            title: "파일이나 메모를 넣어주세요", intro: "파일만 넣어도 괜찮아요. 목차에 맞춰 내용을 정리할게요.",
            steps: ["목차", "자료", "개요 확인"], shared: "전체 자료", optional: "전달할 내용 (선택)",
            placeholder: "예: 자료 공백과 다음 회의의 결정 안건을 강조해주세요.",
            drop: "파일을 여기로 끌어놓으세요", browse: "파일 찾아보기", formats: "PPT · PDF · Excel · Word · 이미지 / 파일당 100MB",
            chapterInputs: "목차별로 따로 넣기 (선택)", toc: "추천 목차", tocHint: "목차 수정은 채팅으로 알려주세요.",
            empty: "기존 정보로 개요 보기", filled: "이 자료로 개요 보기", wait: "자료를 저장했어요. 슬라이드 개요를 기다리고 있어요.",
            waiting: "개요 준비 중", saving: "파일을 첨부하고 있어요", uploaded: "첨부됨", remove: "연결 해제",
            unsupported: "지원되지 않는 파일 형식입니다.", oversized: "파일당 100MB까지 첨부할 수 있어요.", blank: "빈 파일은 첨부할 수 없어요.",
            failed: "첨부 실패", zoneHint: "파일을 첨부 영역에 놓아주세요.", optionalHint: "추가 입력 없이도 기존 정보로 진행할 수 있어요.",
            review: "슬라이드 개요를 확인해주세요", reviewHint: "모든 장표를 검토하고, 수정이 있으면 채팅으로 알려주세요.",
            core: "핵심 메시지", body: "들어갈 내용", visual: "표현 방식", source: "근거·확인 상태", create: "이 개요로 PPT 제작"
        },
        en: {
            title: "Add files or a short note", intro: "Files alone are enough. The agent will organize them into the proposed chapters.",
            steps: ["Chapters", "Materials", "Review"], shared: "Project materials", optional: "A short note (optional)",
            placeholder: "For example: Focus on evidence gaps and decisions needed at the next meeting.",
            drop: "Drop files here", browse: "Browse files", formats: "PPT · PDF · Excel · Word · images / 100MB per file",
            chapterInputs: "Add to individual chapters (optional)", toc: "Proposed chapters", tocHint: "Request chapter changes in chat.",
            empty: "Outline with existing information", filled: "Outline with these materials", wait: "Materials saved. Waiting for the slide outline.",
            waiting: "Preparing outline", saving: "Attaching files", uploaded: "Attached", remove: "Remove association",
            unsupported: "Unsupported file type.", oversized: "The limit is 100MB per file.", blank: "Empty files cannot be attached.",
            failed: "Attachment failed", zoneHint: "Drop files inside an attachment area.", optionalHint: "Continue with existing information without adding anything.",
            review: "Review the complete slide outline", reviewHint: "Review every slide and request changes in chat.",
            core: "Core message", body: "Planned content", visual: "Visual treatment", source: "Evidence / status", create: "Create PPT from this outline"
        },
        zh: {
            title: "添加文件或简短说明", intro: "只提供文件也可以。我们会按目录整理内容。", steps: ["目录", "资料", "大纲确认"],
            shared: "整体资料", optional: "说明（可选）", placeholder: "例如：重点说明资料缺口和下次会议需决定的事项。",
            drop: "将文件拖到这里", browse: "浏览文件", formats: "PPT · PDF · Excel · Word · 图片 / 每个文件100MB",
            chapterInputs: "按章节单独补充（可选）", toc: "建议目录", tocHint: "请在聊天中提出目录修改。",
            empty: "用现有信息准备大纲", filled: "用这些资料准备大纲", wait: "资料已保存，正在等待逐页大纲。", waiting: "大纲准备中",
            saving: "正在添加文件", uploaded: "已添加", remove: "取消关联", unsupported: "不支持此文件格式。", oversized: "每个文件最多100MB。", blank: "不能添加空文件。",
            failed: "添加失败", zoneHint: "请将文件放入附件区域。", optionalHint: "无需补充也可以使用现有信息。",
            review: "确认完整逐页大纲", reviewHint: "请检查所有页面，并在聊天中提出修改。", core: "核心信息", body: "页面内容", visual: "表达形式", source: "依据与状态", create: "按此大纲制作PPT"
        },
        ja: {
            title: "資料または短いメモを追加", intro: "ファイルだけでも大丈夫です。目次に合わせて整理します。", steps: ["目次", "資料", "概要確認"],
            shared: "全体の資料", optional: "メモ（任意）", placeholder: "例：不足資料と次回会議の決定事項を強調してください。",
            drop: "ここにファイルをドロップ", browse: "ファイルを選択", formats: "PPT · PDF · Excel · Word · 画像 / 1ファイル100MB",
            chapterInputs: "章ごとに追加（任意）", toc: "推奨目次", tocHint: "目次の変更はチャットで伝えてください。",
            empty: "既存情報で概要を作成", filled: "この資料で概要を作成", wait: "資料を保存しました。スライド概要を待っています。", waiting: "概要を準備中",
            saving: "資料を添付中", uploaded: "添付済み", remove: "関連付けを解除", unsupported: "対応していない形式です。", oversized: "1ファイル100MBまでです。", blank: "空のファイルは添付できません。",
            failed: "添付失敗", zoneHint: "添付領域にファイルをドロップしてください。", optionalHint: "追加なしでも既存情報で進められます。",
            review: "全スライドの概要を確認", reviewHint: "すべてのスライドを確認し、変更はチャットで伝えてください。", core: "中心メッセージ", body: "掲載内容", visual: "表現方法", source: "根拠・状態", create: "この概要でPPT制作"
        }
    };
    function node(tag, text, cls) {
        var element = document.createElement(tag);
        if (text != null) element.textContent = String(text);
        if (cls) element.className = cls;
        return element;
    }
    function words(lang) { return WORDS[lang] || WORDS.en; }
    function send(url, options) {
        return fetch(url, options).then(function (response) {
            return response.json().then(function (value) {
                if (!response.ok) throw new Error(value.error || "Request failed");
                return value;
            });
        });
    }
    function status(text) {
        var host = document.getElementById("confirm-status");
        host.setAttribute("role", "status"); host.setAttribute("aria-live", "polite");
        host.textContent = text;
    }
    function state(info) {
        if (savedState && savedState.revision === info.view_revision) return savedState;
        savedState = {revision: info.view_revision, entries: {}, files: {}, errors: {}, submitted: false};
        (info.chapters || []).concat([{id: "shared"}]).forEach(function (chapter) {
            savedState.entries[chapter.id] = {chapter_id: chapter.id, text: "", attachments: []};
            savedState.errors[chapter.id] = [];
        });
        var prior = info.saved_response;
        ((prior && prior.files) || []).concat(info.pending_attachments || []).forEach(function (file) {
            savedState.files[file.id] = file;
        });
        if (prior && prior.revision === info.view_revision) {
            savedState.submitted = prior.status === "materials_submitted_not_approved";
            (prior.entries || []).forEach(function (entry) {
                if (savedState.entries[entry.chapter_id]) savedState.entries[entry.chapter_id] = JSON.parse(JSON.stringify(entry));
            });
        } else {
            (info.pending_attachments || []).forEach(function (file) {
                var entry = savedState.entries[file.chapter_id];
                if (entry && entry.attachments.indexOf(file.id) < 0) entry.attachments.push(file.id);
            });
        }
        return savedState;
    }
    function entries(data) {
        return Object.keys(data.entries).map(function (id) { return data.entries[id]; }).filter(function (entry) {
            return entry.text.trim() || entry.attachments.length;
        });
    }
    function refresh() {
        redraw.forEach(function (draw) { draw(); });
        if (!activeInfo) return;
        var w = words(activeLang), data = state(activeInfo), button = document.getElementById("btn-confirm");
        button.textContent = data.submitted ? w.waiting : entries(data).length ? w.filled : w.empty;
        button.disabled = pending > 0 || data.submitted;
        if (data.submitted) status(w.wait);
        else if (pending) status(w.saving + " · " + pending);
        else {
            var errors = Object.keys(data.errors).reduce(function (count, id) { return count + data.errors[id].length; }, 0);
            status(errors ? w.failed + " · " + errors : "");
        }
    }
    function steps(active, w) {
        var host = node("div", null, "intake-steps"); host.setAttribute("role", "list");
        w.steps.forEach(function (title, i) {
            var item = node("span", (i + 1) + "  " + title, i + 1 === active ? "is-active" : "");
            item.setAttribute("role", "listitem");
            if (i + 1 === active) item.setAttribute("aria-current", "step");
            host.appendChild(item);
        });
        return host;
    }
    function upload(selected, chapter, info) {
        var data = state(info), item = data.entries[chapter.id], w = words(activeLang);
        if (data.submitted) return;
        var valid = [];
        Array.prototype.slice.call(selected || []).forEach(function (file) {
            var extension = "." + file.name.split(".").pop().toLowerCase(), problem = null;
            if (ACCEPT.split(",").indexOf(extension) < 0) problem = w.unsupported;
            else if (file.size > MAX_BYTES) problem = w.oversized;
            else if (!file.size) problem = w.blank;
            if (problem) data.errors[chapter.id].push({name: file.name, message: problem});
            else valid.push(file);
        });
        pending += valid.length; refresh();
        valid.forEach(function (file) {
            uploadQueue = uploadQueue.then(function () {
                var body = new FormData();
                body.append("revision", info.view_revision); body.append("chapter_id", chapter.id); body.append("file", file);
                return send("/api/intake/upload", {method: "POST", body: body}).then(function (result) {
                    data.files[result.file.id] = result.file;
                    if (item.attachments.indexOf(result.file.id) < 0) item.attachments.push(result.file.id);
                }).catch(function (error) {
                    data.errors[chapter.id].push({name: file.name, message: error.message});
                }).finally(function () { pending -= 1; refresh(); });
            });
        });
    }
    function editor(chapter, info, w, shared) {
        var data = state(info), item = data.entries[chapter.id];
        var host = shared ? node("section", null, "intake-shared") : node("details", null, "intake-chapter");
        if (!shared) {
            host.appendChild(node("summary", chapter.title));
            if (chapter.purpose) host.appendChild(node("p", chapter.purpose, "content-intake-note"));
        }
        var zone = node("div", null, "intake-dropzone");
        zone.tabIndex = 0; zone.setAttribute("role", "group"); zone.setAttribute("aria-label", chapter.title + " · " + w.drop);
        zone.dataset.chapterId = chapter.id;
        var mark = node("span", "+", "intake-drop-mark"); mark.setAttribute("aria-hidden", "true"); zone.appendChild(mark);
        zone.appendChild(node("strong", w.drop));
        zone.appendChild(node("span", w.formats, "intake-drop-formats"));
        var files = node("input", null, "intake-file-input"); files.type = "file"; files.multiple = true; files.accept = ACCEPT;
        files.setAttribute("aria-label", chapter.title + " · " + w.browse);
        var browse = node("button", w.browse, "intake-browse"); browse.type = "button";
        browse.addEventListener("click", function () { files.click(); });
        zone.addEventListener("keydown", function (event) {
            if (event.target === zone && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); if (!data.submitted) files.click(); }
        });
        zone.appendChild(browse); zone.appendChild(files); host.appendChild(zone);
        files.addEventListener("change", function () { var chosen = Array.prototype.slice.call(files.files || []); files.value = ""; upload(chosen, chapter, info); });
        var depth = 0;
        function fileDrag(event) { return event.dataTransfer && Array.prototype.indexOf.call(event.dataTransfer.types || [], "Files") >= 0; }
        zone.addEventListener("dragenter", function (event) {
            if (!fileDrag(event)) return; event.preventDefault(); event.stopPropagation();
            if (!data.submitted) { depth += 1; zone.classList.add("is-dragging"); }
        });
        zone.addEventListener("dragover", function (event) {
            if (!fileDrag(event)) return; event.preventDefault(); event.stopPropagation();
            event.dataTransfer.dropEffect = data.submitted ? "none" : "copy";
        });
        zone.addEventListener("dragleave", function (event) {
            event.stopPropagation(); depth = Math.max(0, depth - 1); if (!depth) zone.classList.remove("is-dragging");
        });
        zone.addEventListener("drop", function (event) {
            event.preventDefault(); event.stopPropagation(); depth = 0; zone.classList.remove("is-dragging");
            if (event.dataTransfer && !data.submitted) upload(event.dataTransfer.files, chapter, info);
        });
        var list = node("ul", null, "intake-file-list"); host.appendChild(list);
        var errors = node("div", null, "intake-upload-errors"); errors.setAttribute("role", "status"); host.appendChild(errors);
        function drawFiles() {
            list.replaceChildren();
            item.attachments.forEach(function (id) {
                var file = data.files[id], li = node("li"), name = file ? file.name : id;
                var badge = node("span", name.split(".").pop().toUpperCase(), "intake-file-badge"); badge.setAttribute("aria-hidden", "true");
                var label = node("span", name, "intake-file-name"); label.title = name;
                var remove = node("button", "×", "intake-remove"); remove.type = "button";
                remove.setAttribute("aria-label", w.remove + " · " + name); remove.disabled = data.submitted;
                remove.addEventListener("click", function () { item.attachments = item.attachments.filter(function (value) { return value !== id; }); refresh(); });
                li.appendChild(badge); li.appendChild(label); li.appendChild(node("span", w.uploaded, "intake-file-status")); li.appendChild(remove); list.appendChild(li);
            });
            errors.replaceChildren();
            data.errors[chapter.id].forEach(function (failure, index) {
                var row = node("div", null, "intake-upload-error"), dismiss = node("button", "×", "intake-remove");
                row.appendChild(node("span", failure.name + " · " + failure.message));
                dismiss.type = "button"; dismiss.setAttribute("aria-label", w.remove + " · " + failure.name);
                dismiss.disabled = data.submitted;
                dismiss.addEventListener("click", function () { data.errors[chapter.id].splice(index, 1); refresh(); });
                row.appendChild(dismiss); errors.appendChild(row);
            });
            files.disabled = data.submitted; browse.disabled = data.submitted;
            zone.classList.toggle("is-locked", data.submitted); zone.tabIndex = data.submitted ? -1 : 0;
        }
        redraw.push(drawFiles); drawFiles();
        var noteLabel = node("label", w.optional), notes = node("textarea", null, "text-input intake-notes");
        notes.rows = shared ? 2 : 3; notes.value = item.text;
        notes.placeholder = chapter.input_hint || (shared ? w.placeholder : (chapter.requests || [])[0] || w.placeholder);
        notes.setAttribute("aria-label", chapter.title + " · " + w.optional); notes.disabled = data.submitted;
        notes.addEventListener("input", function () { item.text = notes.value; refresh(); });
        noteLabel.appendChild(notes); host.appendChild(noteLabel);
        return host;
    }
    function poll(info, onUpdate) {
        if (pollTimer) clearTimeout(pollTimer);
        pollTimer = setTimeout(function () {
            send("/api/recommendations", {cache: "no-store"}).then(function (payload) {
                var next = payload.content_intake || {};
                if (next.phase === "review" || (next.view_revision && next.view_revision !== info.view_revision)) { onUpdate(payload); return; }
                poll(info, onUpdate);
            }).catch(function (error) { status(error.message); poll(info, onUpdate); });
        }, 1800);
    }
    function renderMaterials(host, info, lang, onUpdate) {
        activeInfo = info; activeLang = lang; redraw = [];
        var w = words(lang), data = state(info), card = node("section", null, "content-intake intake-materials");
        card.appendChild(steps(2, w));
        if (info.title) card.appendChild(node("p", info.title, "intake-context"));
        card.appendChild(node("h2", w.title)); card.appendChild(node("p", w.intro, "intake-intro"));
        var layout = node("div", null, "intake-workspace"), main = node("div", null, "intake-main");
        main.appendChild(editor({id: "shared", title: w.shared}, info, w, true));
        var toc = node("aside", null, "intake-toc"); toc.appendChild(node("h3", w.toc));
        var list = node("ol"); (info.chapters || []).forEach(function (chapter) { list.appendChild(node("li", chapter.title)); }); toc.appendChild(list);
        toc.appendChild(node("p", w.tocHint, "content-intake-note")); layout.appendChild(main); layout.appendChild(toc); card.appendChild(layout);
        var more = node("details", null, "intake-detail"); more.appendChild(node("summary", w.chapterInputs));
        (info.chapters || []).forEach(function (chapter) { more.appendChild(editor(chapter, info, w, false)); }); card.appendChild(more);
        card.appendChild(node("p", w.optionalHint, "intake-optional-hint")); host.appendChild(card); refresh();
        if (data.submitted && onUpdate) poll(info, onUpdate);
        return data.submitted ? w.waiting : entries(data).length ? w.filled : w.empty;
    }
    function renderReview(host, info, lang) {
        activeInfo = null; redraw = [];
        if (pollTimer) clearTimeout(pollTimer);
        var w = words(lang), card = node("section", null, "content-intake intake-review");
        card.appendChild(steps(3, w)); card.appendChild(node("h2", w.review + " (" + (info.slides || []).length + ")"));
        card.appendChild(node("p", w.reviewHint, "intake-intro"));
        var chapterTitles = {}; (info.chapters || []).forEach(function (chapter) { chapterTitles[chapter.id] = chapter.title; });
        (info.slides || []).forEach(function (slide) {
            var row = node("article", null, "intake-slide");
            row.appendChild(node("p", chapterTitles[slide.chapter_id] || slide.chapter_id, "content-intake-note"));
            row.appendChild(node("h3", String(slide.page).padStart(2, "0") + " · " + slide.title));
            row.appendChild(node("p", w.core + ": " + slide.core_message, "intake-core"));
            row.appendChild(node("h4", w.body)); var list = node("ul");
            (slide.content || []).forEach(function (text) { list.appendChild(node("li", text)); }); row.appendChild(list);
            var meta = node("div", null, "intake-slide-meta"); meta.appendChild(node("p", w.visual + ": " + slide.visual));
            meta.appendChild(node("p", w.source + ": " + slide.source_summary, "content-intake-note")); row.appendChild(meta); card.appendChild(row);
        });
        if (info.approval_error) card.appendChild(node("p", info.approval_error, "intake-error"));
        (info.limitations || []).forEach(function (value) { card.appendChild(node("p", value, "content-intake-note")); });
        Object.keys(info.omitted_chapters || {}).forEach(function (id) { card.appendChild(node("p", id + ": " + info.omitted_chapters[id], "content-intake-note")); });
        host.appendChild(card); return w.create;
    }
    function submitMaterials(info, lang, onUpdate) {
        var w = words(lang), data = state(info), button = document.getElementById("btn-confirm");
        if (pending || data.submitted) { refresh(); return; }
        button.disabled = true;
        var selected = entries(data);
        send("/api/intake/materials", {method: "POST", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({revision: info.view_revision, additional_information: selected.length ? "yes" : "no", entries: selected})
        }).then(function () {
            data.submitted = true;
            document.querySelectorAll(".intake-materials input, .intake-materials textarea, .intake-materials button").forEach(function (element) { element.disabled = true; });
            refresh(); status(w.wait); poll(info, onUpdate);
        }).catch(function (error) { button.disabled = false; status(error.message); });
    }
    // Prevent browser navigation when a file misses the drop area. Text drags remain normal.
    ["dragover", "drop"].forEach(function (type) {
        document.addEventListener(type, function (event) {
            if (!document.body.classList.contains("intake-focus") || !event.dataTransfer || Array.prototype.indexOf.call(event.dataTransfer.types || [], "Files") < 0) return;
            event.preventDefault();
            if (type === "drop" && activeInfo) status(words(activeLang).zoneHint);
        });
    });
    window.PPTContentIntake = {
        renderMaterials: renderMaterials, renderReview: renderReview, submitMaterials: submitMaterials,
        isBusy: function () { return pending > 0 || Boolean(activeInfo && savedState && savedState.submitted); }
    };
})();
