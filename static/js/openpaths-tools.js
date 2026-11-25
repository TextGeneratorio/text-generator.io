(function () {
    "use strict";
    var root = document.getElementById("opt-root");
    if (!root) return;
    var kind = root.dataset.kind, tool = root.dataset.tool;
    var $ = function (id) { return document.getElementById(id); };
    var form = $("opt-form"), model = $("opt-model"), note = $("opt-model-note"), prompt = $("opt-prompt");
    var go = $("opt-go"), status = $("opt-status"), out = $("opt-out");
    var models = [], cost = {};

    function fail(msg) {
        status.classList.add("is-error");
        status.textContent = msg;
        if (/log in/i.test(msg)) status.innerHTML = '<a href="/login?next=' + encodeURIComponent(location.pathname) + '">Log in</a> to run this tool.';
    }
    function label() {
        var m = models.find(function (x) { return x.id === model.value; }) || {};
        note.textContent = (m.note || "") + (m.resolution ? " · " + m.resolution : "");
        var c;
        if (kind === "image") c = m.credits_per_image;
        else if (kind === "video") c = m.credits_per_second * Number($("opt-seconds").value || 5);
        go.textContent = c ? "Generate (" + c + " credits)" : kind === "chat" ? "Run" : "Generate";
        if (kind === "video") {
            var needs = m.mode === "image";
            $("opt-image").hidden = !needs; $("opt-image-label").hidden = !needs;
        }
    }
    function post(url, body) {
        return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
            .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { if (!r.ok) throw new Error(d.detail || "Request failed."); return d; }); });
    }
    function show(el) { out.hidden = false; out.replaceChildren(el); }

    fetch("/api/tools/openpaths/models").then(function (r) { return r.json(); }).then(function (c) {
        cost = c;
        models = kind === "image" ? c.images : kind === "video" ? c.videos : c.chat;
        models.forEach(function (m) {
            var o = document.createElement("option");
            o.value = m.id;
            o.textContent = m.name + (kind === "video" ? (m.mode === "image" ? " (image to video)" : " (text to video)") : "");
            model.appendChild(o);
        });
        if (kind === "chat") {
            var t = c.tools[tool] || {};
            prompt.placeholder = t.placeholder || "";
            model.value = t.default_model || model.value;
        } else {
            prompt.value = kind === "image" ? "A quiet glass cabin in a misty pine forest at blue hour, cinematic photography" : "A paper boat drifting down a rain-soaked neon street, slow cinematic dolly shot";
        }
        label();
    });
    model.addEventListener("change", label);
    if ($("opt-seconds")) $("opt-seconds").addEventListener("input", label);

    function poll(jobId) {
        status.textContent = "Rendering video… this can take a few minutes.";
        fetch("/api/tools/openpaths/video/" + jobId).then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.detail || "Status check failed."); return d; }); })
            .then(function (d) {
                if (d.status === "completed") {
                    var v = document.createElement("video");
                    v.src = d.video_url; v.controls = true; v.autoplay = true; v.loop = true;
                    show(v); status.textContent = "Done."; go.disabled = false;
                } else if (d.status === "failed") {
                    fail((d.error || "Video failed.") + " Credits refunded."); go.disabled = false;
                } else setTimeout(function () { poll(jobId); }, 5000);
            }).catch(function (e) { fail(e.message); go.disabled = false; });
    }

    form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        status.classList.remove("is-error");
        go.disabled = true;
        status.textContent = "Working…";
        var p;
        if (kind === "image") {
            p = post("/api/tools/openpaths/image", { prompt: prompt.value, model: model.value, size: $("opt-size").value }).then(function (d) {
                var img = document.createElement("img"); img.src = d.image_url; img.alt = "Generated image"; show(img);
                status.textContent = "Done. " + d.credits_charged + " credits used.";
            });
        } else if (kind === "video") {
            p = post("/api/tools/openpaths/video", { prompt: prompt.value, model: model.value, seconds: Number($("opt-seconds").value), aspect_ratio: $("opt-aspect").value, image_url: $("opt-image").value }).then(function (d) {
                poll(d.job_id); return "polling";
            });
        } else {
            p = post("/api/tools/openpaths/chat", { tool: tool, model: model.value, messages: [{ role: "user", content: prompt.value }] }).then(function (d) {
                var pre = document.createElement("pre"); pre.textContent = d.text; show(pre);
                status.textContent = "Done. " + d.credits_charged + " credits used.";
            });
        }
        p.then(function (r) { if (r !== "polling") go.disabled = false; }).catch(function (e) { fail(e.message); go.disabled = false; });
    });
})();
