(function () {
    "use strict";

    var root = document.querySelector(".tts-studio");
    if (!root) return;

    var text = document.getElementById("tts-text");
    var menu = document.getElementById("tts-typeahead");
    var characterCount = document.getElementById("tts-character-count");
    var voice = document.getElementById("tts-voice");
    var language = document.getElementById("tts-language");
    var speed = document.getElementById("tts-speed");
    var speedValue = document.getElementById("tts-speed-value");
    var generate = document.getElementById("tts-generate");
    var generateRoute = document.getElementById("tts-generate-route");
    var status = document.getElementById("tts-status");
    var audio = document.getElementById("tts-audio");
    var orb = document.getElementById("tts-voice-orb");
    var routeStatus = document.getElementById("tts-route-status");
    var nowVoice = document.getElementById("tts-now-voice");
    var nowModel = document.getElementById("tts-now-model");
    var format = document.getElementById("tts-format");
    var processing = document.getElementById("tts-processing");
    var billing = document.getElementById("tts-billing");
    var code = document.getElementById("tts-code");
    var codeProvider = document.getElementById("tts-code-provider");
    var creditBalance = document.getElementById("tts-credit-balance");
    var topupButton = document.getElementById("tts-topup");
    var selectedCode = "curl";
    var selectedSuggestion = 0;
    var currentSuggestions = [];
    var accountSecret = "YOUR_API_KEY";
    var creditCents = 0;
    var objectURL = null;

    var modelConfig = {
        kokoro: {
            label: "Kokoro", provider: "Text Generator", model: "kokoro", endpoint: "/api/v1/generate_speech", billing: "Account usage",
            voices: ["af_nicole", "af_heart", "af_bella", "af_sarah", "af_sky", "am_adam", "am_michael", "bf_emma", "bf_isabella", "bm_george", "bm_lewis"]
        },
        supertonic: {
            label: "Supertonic", provider: "Text Generator", model: "supertonic", endpoint: "/api/v1/generate_speech", billing: "Account usage",
            voices: ["F1", "F2", "F3", "F4", "F5", "M1", "M2", "M3", "M4", "M5"]
        },
        "appnz-tts": {
            label: "App.nz TTS", provider: "Text Generator", model: "appnz-tts", endpoint: "/v1/audio/speech", billing: "$0.10 / min · TG credits",
            metered: true, voices: ["eve", "alba", "default", "narrator", "warm", "bright"]
        },
        "pocket-tts": {
            label: "Pocket TTS", provider: "Text Generator", model: "pocket-tts", endpoint: "/v1/audio/speech", billing: "$0.06 / min · TG credits",
            metered: true, voices: ["alba", "anna", "azelma", "caro_davy", "charles", "cosette", "eve", "george", "jane", "jean", "lola", "michael", "rafael", "vera"]
        }
    };

    function LocalBloodhound(words, phrases) {
        this.words = words.slice().sort(function (a, b) { return b[1] - a[1]; });
        this.phrases = phrases || [];
    }

    LocalBloodhound.prototype.search = function (query) {
        var beforeCursor = String(query || "");
        var phraseQuery = beforeCursor.trim().toLowerCase();
        var wordMatch = beforeCursor.match(/([A-Za-z'-]+)$/);
        var prefix = wordMatch ? wordMatch[1].toLowerCase() : "";
        var matches = [];

        if (phraseQuery.length >= 4) {
            this.phrases.forEach(function (phrase, index) {
                if (phrase.toLowerCase().indexOf(phraseQuery) === 0 && phrase.length > phraseQuery.length) {
                    matches.push({ value: phrase, prefix: beforeCursor.trim(), completion: phrase.slice(beforeCursor.trim().length), score: 20000 - index, phrase: true });
                }
            });
        }

        if (prefix.length) {
            this.words.forEach(function (entry) {
                if (matches.length >= 6) return;
                if (entry[0].indexOf(prefix) === 0 && entry[0] !== prefix) {
                    matches.push({ value: entry[0], prefix: prefix, completion: entry[0].slice(prefix.length), score: entry[1], phrase: false });
                }
            });
        }
        return matches.sort(function (a, b) { return b.score - a.score; }).slice(0, 6);
    };

    var bloodhound = new LocalBloodhound(window.TTS_AUTOCOMPLETE_WORDS || [], window.TTS_AUTOCOMPLETE_PHRASES || []);
    window.ttsBloodhound = bloodhound;

    function closeTypeahead() {
        menu.hidden = true;
        text.setAttribute("aria-expanded", "false");
        text.removeAttribute("aria-activedescendant");
        currentSuggestions = [];
    }

    function paintTypeahead() {
        menu.innerHTML = "";
        currentSuggestions.forEach(function (suggestion, index) {
            var item = document.createElement("button");
            item.type = "button";
            item.id = "tts-suggestion-" + index;
            item.className = "tts-suggestion" + (index === selectedSuggestion ? " is-selected" : "");
            item.setAttribute("role", "option");
            item.setAttribute("aria-selected", String(index === selectedSuggestion));
            item.innerHTML = '<span><small>' + escapeHTML(suggestion.prefix) + '</small><strong>' + escapeHTML(suggestion.completion) + '</strong></span><em>' + (suggestion.phrase ? "phrase" : "local") + '</em>';
            item.addEventListener("mousedown", function (event) {
                event.preventDefault();
                applySuggestion(index);
            });
            menu.appendChild(item);
        });
        menu.hidden = !currentSuggestions.length;
        text.setAttribute("aria-expanded", String(Boolean(currentSuggestions.length)));
        if (currentSuggestions.length) text.setAttribute("aria-activedescendant", "tts-suggestion-" + selectedSuggestion);
    }

    function escapeHTML(value) {
        var node = document.createElement("span");
        node.textContent = value;
        return node.innerHTML;
    }

    function refreshTypeahead() {
        var cursor = text.selectionStart == null ? text.value.length : text.selectionStart;
        currentSuggestions = bloodhound.search(text.value.slice(0, cursor));
        selectedSuggestion = 0;
        paintTypeahead();
    }

    function applySuggestion(index) {
        var suggestion = currentSuggestions[index];
        if (!suggestion) return;
        var cursor = text.selectionStart == null ? text.value.length : text.selectionStart;
        var before = text.value.slice(0, cursor);
        var after = text.value.slice(cursor);
        if (suggestion.phrase) {
            text.value = suggestion.value + (after || "");
            cursor = suggestion.value.length;
        } else {
            var match = before.match(/([A-Za-z'-]+)$/);
            var start = match ? cursor - match[1].length : cursor;
            text.value = text.value.slice(0, start) + suggestion.value + " " + after;
            cursor = start + suggestion.value.length + 1;
        }
        text.setSelectionRange(cursor, cursor);
        updateCharacterCount();
        closeTypeahead();
        text.focus();
    }

    text.addEventListener("input", function () { updateCharacterCount(); refreshTypeahead(); });
    text.addEventListener("click", refreshTypeahead);
    text.addEventListener("blur", function () { window.setTimeout(closeTypeahead, 120); });
    text.addEventListener("keydown", function (event) {
        if (menu.hidden || !currentSuggestions.length) {
            if (event.key === "Tab") refreshTypeahead();
            return;
        }
        if (event.key === "ArrowDown") selectedSuggestion = (selectedSuggestion + 1) % currentSuggestions.length;
        else if (event.key === "ArrowUp") selectedSuggestion = (selectedSuggestion - 1 + currentSuggestions.length) % currentSuggestions.length;
        else if (event.key === "Tab" || event.key === "Enter") { event.preventDefault(); applySuggestion(selectedSuggestion); return; }
        else if (event.key === "Escape") { closeTypeahead(); return; }
        else return;
        event.preventDefault();
        paintTypeahead();
    });

    window.__ttsOpenAutocomplete = function () {
        text.focus();
        refreshTypeahead();
    };

    function selectedModel() {
        return document.querySelector("input[name=tts-model]:checked").value;
    }

    function updateCharacterCount() {
        characterCount.textContent = text.value.length + " / 5000";
    }

    function formatCredits(cents) {
        return "$" + (Number(cents || 0) / 100).toFixed(2);
    }

    function paintCreditBalance() {
        if (!creditBalance) return;
        creditBalance.textContent = formatCredits(creditCents);
        document.querySelectorAll("[data-credit-balance]").forEach(function (el) {
            el.textContent = formatCredits(creditCents);
        });
    }

    function openTopupModal() {
        if (window.showCheckoutDialog) {
            window.showCheckoutDialog("credits", 100);
            return;
        }
        window.location.href = "/account";
    }

    function updateModel() {
        var id = selectedModel();
        var config = modelConfig[id];
        voice.innerHTML = "";
        config.voices.forEach(function (voiceName) {
            var option = document.createElement("option");
            option.value = voiceName;
            option.textContent = voiceName;
            voice.appendChild(option);
        });
        language.disabled = id === "kokoro";
        generateRoute.textContent = config.provider + " · " + config.label;
        codeProvider.textContent = config.metered ? "App.nz via Text Generator" : config.provider;
        billing.textContent = config.billing;
        updateVoiceSummary();
        updateCode();
    }

    function updateVoiceSummary() {
        var config = modelConfig[selectedModel()];
        nowVoice.textContent = voice.value;
        nowModel.textContent = config.label + " · " + config.provider;
    }

    function inferenceBase() {
        return location.hostname === "localhost" || location.hostname === "127.0.0.1"
            ? "http://localhost:9080"
            : "https://api.text-generator.io";
    }

    function codePayload(config) {
        if (config.metered) {
            return { model: config.model, voice: voice.value, input: text.value.slice(0, 90) || "Hello from Text Generator." };
        }
        return { text: text.value.slice(0, 90) || "Hello from Text Generator.", voice: voice.value, language: language.value, speed: Number(speed.value), steps: 4 };
    }

    function updateCode() {
        var config = modelConfig[selectedModel()];
        var payload = JSON.stringify(codePayload(config), null, 2);
        var endpoint = "https://api.text-generator.io" + config.endpoint;
        var authHeader = "secret: YOUR_API_KEY";
        var ext = config.metered ? "mp3" : "wav";
        if (selectedCode === "javascript") {
            code.textContent = 'const response = await fetch("' + endpoint + '", {\n  method: "POST",\n  headers: {\n    "Content-Type": "application/json",\n    "secret": "YOUR_API_KEY"\n  },\n  body: JSON.stringify(' + payload + ')\n});\nconst audio = await response.blob();';
        } else if (selectedCode === "python") {
            code.textContent = 'import requests\n\nresponse = requests.post(\n    "' + endpoint + '",\n    headers={"secret": "YOUR_API_KEY"},\n    json=' + payload.replace(/true/g, "True").replace(/false/g, "False") + ',\n)\nopen("speech.' + ext + '", "wb").write(response.content)';
        } else {
            code.textContent = 'curl "' + endpoint + '" \\\n  -H "Content-Type: application/json" \\\n  -H "' + authHeader + '" \\\n  -d \'' + payload.replace(/\n/g, "\n  ") + '\' \\\n  --output speech.' + ext;
        }
    }

    document.querySelectorAll("input[name=tts-model]").forEach(function (input) { input.addEventListener("change", updateModel); });
    document.querySelectorAll("[data-tts-code]").forEach(function (tab) {
        tab.addEventListener("click", function () {
            selectedCode = tab.getAttribute("data-tts-code");
            document.querySelectorAll("[data-tts-code]").forEach(function (item) { item.classList.toggle("is-active", item === tab); });
            updateCode();
        });
    });
    voice.addEventListener("change", function () { updateVoiceSummary(); updateCode(); });
    language.addEventListener("change", updateCode);
    speed.addEventListener("input", function () { speedValue.textContent = Number(speed.value).toFixed(1) + "×"; updateCode(); });
    text.addEventListener("input", updateCode);
    if (topupButton) topupButton.addEventListener("click", openTopupModal);

    document.getElementById("tts-example").addEventListener("click", function () {
        text.value = "Imagine a voice that sounds clear, warm, and human. With Text Generator, your next story is ready to be heard.";
        updateCharacterCount();
        updateCode();
        text.focus();
    });

    function loadCreditBalance() {
        return fetch("/api/credits/balance").then(function (response) { return response.ok ? response.json() : null; }).then(function (data) {
            if (!data) return;
            creditCents = Number((data.balance && data.balance.total) || data.credit_balance_cents || 0);
            paintCreditBalance();
        }).catch(function () {});
    }

    if (!window.skip_auth_hydration) {
        fetch("/api/current-user").then(function (response) { return response.ok ? response.json() : null; }).then(function (user) {
            if (user && user.secret) {
                accountSecret = user.secret;
                creditCents = Number(user.credit_balance_cents || user.free_credits || 0);
                paintCreditBalance();
                status.textContent = "Signed in · balance " + formatCredits(creditCents) + " · ready to generate speech.";
            }
        }).catch(function () {});

        loadCreditBalance();
    }

    generate.addEventListener("click", async function () {
        var config = modelConfig[selectedModel()];
        if (!text.value.trim()) { status.textContent = "Write something to speak first."; status.classList.add("is-error"); return; }
        if (accountSecret === "YOUR_API_KEY") {
            status.innerHTML = '<a href="/login?next=%2Ftext-to-speech">Log in</a> to generate speech.';
            status.classList.add("is-error");
            return;
        }
        if (config.metered && creditCents <= 0) {
            status.textContent = "Add Text Generator credits for this metered route.";
            status.classList.add("is-error");
            openTopupModal();
            return;
        }

        status.classList.remove("is-error");
        status.textContent = "Synthesizing with " + config.label + "…";
        routeStatus.textContent = "Generating";
        generate.disabled = true;
        orb.classList.add("is-active");
        processing.textContent = "Generating";

        var headers = { "Content-Type": "application/json" };
        var endpoint;
        var body;
        if (config.metered) {
            endpoint = "/api/tools/text-to-speech/generate";
            body = {
                model: config.model,
                input: text.value,
                voice: voice.value,
                language: language.value,
                speed: Number(speed.value),
                response_format: "mp3"
            };
        } else {
            headers.secret = accountSecret;
            endpoint = inferenceBase() + config.endpoint;
            body = codePayload(config);
            body.text = text.value;
        }

        try {
            var response = await fetch(endpoint, { method: "POST", headers: headers, body: JSON.stringify(body) });
            if (!response.ok) {
                var detail = await response.json().catch(function () { return {}; });
                var message = detail.detail || detail.error || "Speech generation failed (" + response.status + ").";
                if (response.status === 402 || /credit|top up|subscribe/i.test(String(message))) {
                    openTopupModal();
                }
                throw new Error(message);
            }
            var charged = Number(response.headers.get("X-Credits-Charged") || 0);
            var balanceHeader = response.headers.get("X-Credit-Balance");
            if (balanceHeader != null) {
                creditCents = Number(balanceHeader);
                paintCreditBalance();
            } else if (charged > 0) {
                creditCents = Math.max(0, creditCents - charged);
                paintCreditBalance();
            }
            var blob = await response.blob();
            if (objectURL) URL.revokeObjectURL(objectURL);
            objectURL = URL.createObjectURL(blob);
            audio.src = objectURL;
            await audio.play().catch(function () {});
            format.textContent = blob.type.indexOf("mpeg") >= 0 ? "MP3" : blob.type.indexOf("ogg") >= 0 ? "OGG" : "WAV";
            processing.textContent = "Complete";
            routeStatus.textContent = "Playing";
            status.textContent = charged
                ? "Speech generated · charged " + charged + " credit" + (charged === 1 ? "" : "s") + " · balance " + formatCredits(creditCents) + "."
                : "Speech generated successfully.";
        } catch (error) {
            status.classList.add("is-error");
            status.textContent = error.message;
            processing.textContent = "Failed";
            routeStatus.textContent = "Error";
            orb.classList.remove("is-active");
        } finally {
            generate.disabled = false;
        }
    });

    audio.addEventListener("play", function () { orb.classList.add("is-active"); routeStatus.textContent = "Playing"; });
    audio.addEventListener("pause", function () { orb.classList.remove("is-active"); if (!audio.ended) routeStatus.textContent = "Paused"; });
    audio.addEventListener("ended", function () { orb.classList.remove("is-active"); routeStatus.textContent = "Ready"; });

    if (!window.skip_auth_hydration && new URLSearchParams(location.search).get("credits") === "success") {
        status.textContent = "Credits topped up. Ready to generate speech.";
        loadCreditBalance();
    }

    updateCharacterCount();
    updateModel();
})();
