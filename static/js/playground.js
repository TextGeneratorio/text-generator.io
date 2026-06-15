
    var programmingLanguage = 'py';
    var allProgrammingLanguages = ['py', 'js', 'bash'];
    var apiCallTypeDisplay = 'generation';

    function hideAllCodeSnippets() {
        allProgrammingLanguages.forEach(function(language) {
            $(`#code-snippet-${language}`).hide();
            $(`#code-snippet-${language}-embed`).hide();
        });
    }
    function displayTextGenerationCode() {
        hideAllCodeSnippets();
        $(`#code-snippet-${programmingLanguage}`).show();
        apiCallTypeDisplay = 'generation';

        return false;
    }

    function displayEmbedCode() {
        hideAllCodeSnippets()
        $(`#code-snippet-${programmingLanguage}-embed`).show();
        apiCallTypeDisplay = 'embed';

        return false;
    }

    function changeLanguage(newLanguage) {
        programmingLanguage = newLanguage;
        if(apiCallTypeDisplay === 'generation') {
            displayTextGenerationCode();
        } else {
            displayEmbedCode();
        }
        return false;
    }


    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    var secret = '';
    var multimodalAttachments = [];
    var multimodalUploadInFlight = false;
    var setUrl = function () {
        // set the url to generate settings so users can share and come back to the same place

        // change location to generationSettings url params
        var urlParams = new URLSearchParams(generationSettings);
        history.replaceState(null, null, '/playground?' + urlParams.toString());


    }
    var setupFromUrl = function () {
        const params = Object.fromEntries(new URLSearchParams(location.search));
        if (!params.text) {
            return;
        }
        let stopSequencesArray = params.stop_sequences;
        if (stopSequencesArray) {
            stopSequencesArray = stopSequencesArray.split(',');
        } else {
            stopSequencesArray = [];
        }
        function nanDefault(num, defaultValueIfNan) {
          if (isNaN(num)) {
            return defaultValueIfNan;
          }
          return num
        }
        function boolDefault(value, defaultValueIfInvalid) {
            if (typeof value === 'undefined' || value === null || value === '') {
                return defaultValueIfInvalid;
            }
            if (typeof value === 'boolean') {
                return value;
            }
            var normalized = String(value).toLowerCase();
            if (normalized === 'true' || normalized === '1' || normalized === 'yes' || normalized === 'on') {
                return true;
            }
            if (normalized === 'false' || normalized === '0' || normalized === 'no' || normalized === 'off') {
                return false;
            }
            return defaultValueIfInvalid;
        }
        generationSettings = {
            "text": params.text,
            "number_of_results": nanDefault(parseInt(params.number_of_results), presets['Example use cases'].number_of_results),
            "max_length": nanDefault(parseInt(params.max_length), presets['Example use cases'].max_length),
            "max_sentences": nanDefault(parseInt(params.max_sentences), presets['Example use cases'].max_sentences),
            "min_probability": nanDefault(parseFloat(params.min_probability), presets['Example use cases'].min_probability),
            "stop_sequences": stopSequencesArray,
            "top_p": nanDefault(parseFloat(params.top_p), presets['Example use cases'].top_p),
            "top_k": nanDefault(parseInt(params.top_k), presets['Example use cases'].top_k),
            "temperature": nanDefault(parseFloat(params.temperature), presets['Example use cases'].temperature),
            "repetition_penalty": nanDefault(parseFloat(params.repetition_penalty), presets['Example use cases'].repetition_penalty),
            "seed": nanDefault(parseInt(params.seed), presets['Example use cases'].seed),
            "model": params.model || presets['Example use cases'].model,
            "enable_thinking": boolDefault(params.enable_thinking, presets['Example use cases'].enable_thinking),
            "system_message": params.system_message || presets['Example use cases'].system_message,
        }
        setPreset(generationSettings);
    }
    var presets = {
        "Example use cases": {
            "text": "",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0,
            "model": "best",
            "enable_thinking": false,
            "system_message": ""
        },
        "Elves vs Goblins": {
            "text": "The battle between the elves and goblins has begun,",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0
        },
        "Complex Summarization": {
            "text": "In February, shortly after a NASA oversight panelist revealed that SpaceX was targeting 52 launches in 2022, CEO Elon Musk confirmed that the company’s goal was for “Falcon [to] launch about once a week” throughout the year. In October 2020, continuing a tradition of extremely ambitious SpaceX launch cadence targets, Musk had also tweeted that “a lot of improvements” would need to be made to achieve his goal of 48 launches – an average of four launches per month – in 2021. Ultimately, SpaceX fell well short of that target, but did set a new annual record of 31 launches in one year, breaking its 2020 record of 26 launches by about 20%. However, perhaps even more important than the new record was the fact that SpaceX was able to complete six launches in four weeks at the end of 2021.\n\nin summary:",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 2,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.03,
            "seed": 0
        },
        "Recent Events - Stock": {
            "text": "in 2022 the stock market has been ",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0.1,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0
        },
        "Autocomplete": {
            "text": "Hi i'm bored so looking",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0.7,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0
        },
        "Python Code Autocomplete": {
            "text": "def random_string(size=6, chars=string.ascii_letters + string.digits):\n    \"\"\" Generate random string \"\"\"\n    return ",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0.1,
            "stop_sequences": [],
            "top_p": 0.5,
            "top_k": 40,
            "temperature": 0.9,
            "repetition_penalty": 1.17,
            "seed": 0,
            "model": "best",
            "enable_thinking": false,
            "system_message": "You are an autocomplete engine for Python code. Continue exactly from the cursor with valid Python code only. No explanations or markdown.",
        },
        "Python Function Generation": {
            "text": "def can_balance(a):\n    \"\"\"return if a can be split into two arrays with equal sum\"\"\"\n    ",
            "number_of_results": 1,
            "max_length": 220,
            "max_sentences": 0,
            "min_probability": 0.0,
            "stop_sequences": [],
            "top_p": 0.45,
            "top_k": 40,
            "temperature": 0.2,
            "repetition_penalty": 1.08,
            "seed": 0,
            "model": "best",
            "enable_thinking": false,
            "system_message": "You are an expert Python engineer. Continue the user's code directly. Output code only, with no explanation and no markdown fences.",
        },
        "PyTorch Module Generation": {
            "text": "import torch\nimport torch.nn as nn\n\nclass TinyTextGenerator(nn.Module):\n    def __init__(self, vocab_size: int, d_model: int = 256):\n        super().__init__()\n        self.embed = nn.Embedding(vocab_size, d_model)\n        self.lm_head = nn.Linear(d_model, vocab_size)\n\n    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:\n        x = self.embed(input_ids)\n",
            "number_of_results": 1,
            "max_length": 260,
            "max_sentences": 0,
            "min_probability": 0.0,
            "stop_sequences": [],
            "top_p": 0.5,
            "top_k": 40,
            "temperature": 0.25,
            "repetition_penalty": 1.08,
            "seed": 0,
            "model": "best",
            "enable_thinking": false,
            "system_message": "You are an expert PyTorch engineer. Continue the code with valid, runnable PyTorch 2.x Python code only. No prose and no markdown.",
        },
        "Review Classification": {
            "text": "What a really awesome game, would play again\n review star rating: ",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0.7,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0
        },
        "Multi lingual Generation": {
            "text": "हेलो यह कैसा चल रहा है",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 4,
            "min_probability": 0,
            "stop_sequences": [],
            "top_p": 0.9,
            "top_k": 40,
            "temperature": 0.7,
            "repetition_penalty": 1.17,
            "seed": 0
        },
        "Java Code Generation": {
            "text": "class CanBalance {\n    /* \n     * return true if the array can be balanced into two arrays with the same sum\n     */\n    public static boolean canBalance(rocks int[]) {\n        if",
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "min_probability": 0.3,
            "stop_sequences": [],
            "top_p": 0.5,
            "top_k": 40,
            "temperature": 0.9,
            "repetition_penalty": 1.17,
            "seed": 0,
        },
        "C sharp Code Generation": {
            "text": "using System.Collections;\nusing System.Collections.Generic;\nusing UnityEngine;\n\nnamespace DYP\n{\n    public class Waypoints2D : MonoBehaviour\n    {\n\n        [SerializeField]\n        private List m_Points = new List();\n        public List Points { get { return m_Points; } }\n\n        public int Count { get { return m_Points.Count; } }\n\n        public Vector2 At(int index)\n        {\n            return",
            "min_probability": 0.25,
            "top_p": 0.3,
            "number_of_results": 1,
            "max_length": 100,
            "max_sentences": 1,
            "stop_sequences": [],
            "top_k": 40,
            "temperature": 0.9,
            "repetition_penalty": 1.17,
            "seed": 0,
        },// paper generation - thispaperdoesnotexist - hosting generated content from lang generator
    }

    var preset_names = Object.keys(presets);

    function setPreset(preset) {
        setTextUI(preset.text);
        setTextData(preset.text);
        $('#slider-number-of-results').val(preset.number_of_results);
        $('#slider-max-length').val(preset.max_length);
        $('#slider-max-sentences').val(preset.max_sentences);
        $('#slider-min-probability').val(preset.min_probability);

        $('#select-stop-sequences').val(preset.stop_sequences).change();

        $('#slider-top-p').val(preset.top_p);
        $('#slider-top-k').val(preset.top_k);
        $('#slider-temperature').val(preset.temperature);
        $('#slider-repetition-penalty').val(preset.repetition_penalty);
        $('#slider-seed').val(preset.seed);
        $('#system-message').val(preset.system_message || "");
        $('#enable-thinking').prop('checked', !!preset.enable_thinking);
        setGenerationSettingsUI(preset);
    }

    $(document).ready(function () {
        var presetOptions = $.map(preset_names, function (key) {
            return '<option value="' + key + '">' + key + '</option>';
        });
        $('#preset').html(presetOptions);
        $('#preset').select2({
            data: preset_names
        });
        // on change
        $('#preset').on('change', function (e) {
            var preset = presets[$(this).val()];
            setPreset(preset);
        });
    });

    var generationSettings = {};

    var setTextUI = function (value) {
        editor.setValue(value);
    }
    var setTextData = function (value) {
        generationSettings['text'] = value
        setUrl(generationSettings)
    }
    var setNumberOfResults = function (value) {
        value = parseInt(value);
        $('#slider-number-of-results-tooltip').html(`Number of Results: ${value}`);
        generationSettings['number_of_results'] = value
        setUrl(generationSettings)
    }
    var setMaxLength = function (value) {
        value = parseInt(value);
        $('#slider-max-length-tooltip').html(`Max Length: ${value}`);
        generationSettings['max_length'] = value
        setUrl(generationSettings)
    }
    var setMaxSentences = function (value) {
        value = parseInt(value);
        $('#slider-max-sentences-tooltip').html(`Max Sentences: ${value}`);
        generationSettings['max_sentences'] = value
        setUrl(generationSettings)
    }
    var setMinProbability = function (value) {
        value = parseFloat(value);
        $('#slider-min-probability-tooltip').html(`Min Probability: ${value.toFixed(2)}`);
        generationSettings['min_probability'] = value
        setUrl(generationSettings)
    }
    var setStopSequences = function (value) {
        // split lines
        values = $('#select-stop-sequences').select2('data');
        values = values.map(function (value) {
            return value.text;
        });
        generationSettings['stop_sequences'] = values
        setUrl(generationSettings)
    }
    var setTopP = function (value) {
        value = parseFloat(value);
        $('#slider-top-p-tooltip').html(`Top P: ${value.toFixed(2)}`);
        generationSettings['top_p'] = value
        setUrl(generationSettings)
    }
    var setTopK = function (value) {
        value = parseInt(value);
        $('#slider-top-k-tooltip').html(`Top K: ${value}`);
        generationSettings['top_k'] = value
        setUrl(generationSettings)
    }
    var setTemperature = function (value) {
        value = parseFloat(value);
        $('#slider-temperature-tooltip').html(`Temperature: ${value.toFixed(2)}`);
        generationSettings['temperature'] = value
        setUrl(generationSettings)
    }
    var setRepetitionPenalty = function (value) {
        value = parseFloat(value);
        $('#slider-repetition-penalty-tooltip').html(`Repetition Penalty: ${value.toFixed(2)}`);
        generationSettings['repetition_penalty'] = value
        setUrl(generationSettings)
    }
    var setSeed = function (value) {
        value = parseInt(value);
        $('#slider-seed-tooltip').html(`Seed: ${value}`);
        generationSettings['seed'] = value
        setUrl(generationSettings)
    }
    var setModel = function (value) {
        if (typeof value !== 'undefined' && value !== null) {
            $('#select-model').val(value);
        }
        value = $('#select-model').val() || 'best';
        $('#model-tooltip').html(`Model: ${value}`);
        generationSettings['model'] = value
        setUrl(generationSettings)
    }
    var setEnableThinking = function (value) {
        value = !!value;
        $('#enable-thinking').prop('checked', value);
        generationSettings['enable_thinking'] = value;
        setUrl(generationSettings);
    }
    var setSystemMessage = function (value) {
        value = value || '';
        $('#system-message').val(value);
        generationSettings['system_message'] = value;
        setUrl(generationSettings);
    }
    if (typeof window !== 'undefined') {
        window.setSystemMessage = setSystemMessage;
    }

    function wrapLinesForLineNumbers(codeEl) {
        // After highlight.js processes, wrap each line in a span for CSS line numbers
        var html = codeEl.innerHTML;
        var lines = html.split('\n');
        codeEl.innerHTML = lines.map(function(line) {
            return '<span class="hljs-line">' + (line || ' ') + '</span>';
        }).join('');
    }

    function copyCodeSnippet(preEl) {
        // Find the visible code element in the dialog
        var dialog = preEl.closest('dialog');
        var codes = dialog.querySelectorAll('.mdl-dialog__content pre code');
        var visibleCode = null;
        for (var i = 0; i < codes.length; i++) {
            if (codes[i].offsetParent !== null) {
                visibleCode = codes[i];
                break;
            }
        }
        var btn = preEl.querySelector('.code-copy-btn');
        if (visibleCode && btn) {
            navigator.clipboard.writeText(visibleCode.textContent).then(function() {
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(function() {
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }, 2000);
            });
        }
    }

    var showCode = function () {

        var generationSettingsFormatted = JSON.stringify(generationSettings, null, 4);
        var generationSettingsCurlFormatted = JSON.stringify(generationSettings, null, 0);
        var toPythonLiteral = function (value, indentLevel) {
            indentLevel = indentLevel || 0;
            var indent = ' '.repeat(indentLevel * 4);
            var nextIndent = ' '.repeat((indentLevel + 1) * 4);

            if (value === null || typeof value === 'undefined') {
                return 'None';
            }
            if (typeof value === 'boolean') {
                return value ? 'True' : 'False';
            }
            if (typeof value === 'number') {
                return Number.isFinite(value) ? String(value) : 'None';
            }
            if (typeof value === 'string') {
                return JSON.stringify(value);
            }
            if (Array.isArray(value)) {
                if (value.length === 0) {
                    return '[]';
                }
                return '[\n' + value.map(function (item) {
                    return nextIndent + toPythonLiteral(item, indentLevel + 1);
                }).join(',\n') + '\n' + indent + ']';
            }
            if (typeof value === 'object') {
                var entries = Object.entries(value);
                if (entries.length === 0) {
                    return '{}';
                }
                return '{\n' + entries.map(function (entry) {
                    var key = entry[0];
                    var item = entry[1];
                    return nextIndent + JSON.stringify(key) + ': ' + toPythonLiteral(item, indentLevel + 1);
                }).join(',\n') + '\n' + indent + '}';
            }
            return JSON.stringify(value);
        };
        var generationSettingsPythonFormatted = toPythonLiteral(generationSettings, 0);
        $('#code-snippet-py').html(`import requests

headers = {"secret": "${secret}"}

data = ${generationSettingsPythonFormatted}

response = requests.post(
   "https://api.text-generator.io/api/v1/generate",
   json=data,
   headers=headers
)

json_response = response.json()

for generation in json_response:
    generated_text = generation["generated_text"][len(data['text']):]
    print(generated_text)
`);
        $('#code-snippet-py-embed').html(`import requests

headers = {"secret": "${secret}"}

data = {
    "text": ${JSON.stringify(generationSettings.text, null, 4) || "\"Test text here\""},
    "num_features": 768
}
response = requests.post(
   "https://api.text-generator.io/api/v1/feature-extraction",
   json=data,
   headers=headers
)

json_response_list = response.json() # the embedding is a list of numbers
`);
        $('#code-snippet-js').html(`var generationSettings = ${generationSettingsFormatted};

var secret = "${secret}";
fetch('https://api.text-generator.io/api/v1/generate', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'secret': secret
    },
    body: JSON.stringify(generationSettings)
}).then(function (response) {
    if (response.ok) {
        return response.json();
    } else {
        console.log(response.text(), response.status + ' - ' + response.statusText);
    }
}).then(function (data) {
    for (var i = 0; i < data.length; i++) {
        var predictedText = data[i]['generated_text'].substring(generationSettings.text.length);
        console.log(predictedText);
    }
}).catch(function (error) {
    console.log(error);
})`);
        $('#code-snippet-js-embed').html(`var generationSettings = {
    "text": ${JSON.stringify(generationSettings.text, null, 4) || "\"Test text here\""},
    "num_features": 768
};

var secret = "${secret}";
fetch('https://api.text-generator.io/api/v1/feature-extraction', {
    method: 'POST',
    headers: {
'Content-Type': 'application/json',
        'secret': secret
    },
    body: JSON.stringify(generationSettings)
}).then(function (response) {
    if (response.ok) {
        return response.json();
    } else {
        console.log(response.text(), response.status + ' - ' + response.statusText);
    }
}).then(function (data) {
    console.log(data); // the embedding is an array of numbers
}).catch(function (error) {
    console.log(error);
})
`);

        $('#code-snippet-bash').html(`curl 'https://api.text-generator.io/api/v1/generate' \\
  -H 'content-type: application/json' \\
  -H 'secret: ${secret}' \\
  --data-raw '${generationSettingsCurlFormatted}' \\
  --compressed`);
        $('#code-snippet-bash-embed').html(`curl 'https://api.text-generator.io/api/v1/feature-extraction' \\
  -H 'content-type: application/json' \\
  -H 'secret: ${secret}' \\
  --data-raw '{"num_features":768,"text": ${JSON.stringify(generationSettings.text, null, 0) || "\"Test text here\""} \\
  --compressed`);
        hljs.highlightAll();
        // Add line number wrapping to all code snippets
        document.querySelectorAll('dialog pre code').forEach(wrapLinesForLineNumbers);
        var dialog = document.querySelector('dialog');
        dialog.close();
        dialog.showModal();
        // Reset copy button
        var copyBtn = dialog.querySelector('.code-copy-btn');
        if (copyBtn) { copyBtn.textContent = 'Copy'; copyBtn.classList.remove('copied'); }
        return false;
    }

    function setGenerationSettingsUI(review) {
        setNumberOfResults(review['number_of_results']);
        setMaxLength(review['max_length']);
        setMaxSentences(review['max_sentences']);
        setMinProbability(review['min_probability']);
        setStopSequences(review['stop_sequences']);
        setTopP(review['top_p']);
        setTopK(review['top_k']);
        setTemperature(review['temperature']);
        setRepetitionPenalty(review['repetition_penalty']);
        setSeed(review['seed']);
        setModel(review['model'] || 'best');
        setEnableThinking(typeof review['enable_thinking'] === 'boolean' ? review['enable_thinking'] : false);
        setSystemMessage(review['system_message'] || '');
    }

    function setupDialog() {
        var dialog = document.querySelector('dialog');
        if (!dialog.showModal) {
            return
            //todo polyfill>?
        }
        dialog.querySelector('.close').addEventListener('click', function () {
            dialog.close();
        });
        // default to Review Classification
        setupFromUrl();
    }

    function normalizePlaygroundResponse(data) {
        if (Array.isArray(data)) {
            return data;
        }
        if (data && data.choices && data.choices[0] && data.choices[0].message) {
            return [{
                generated_text: data.choices[0].message.content || '',
                thinking_content: data.choices[0].message.reasoning_content || null,
                stop_reason: data.choices[0].finish_reason || 'stop'
            }];
        }
        return [];
    }

    function hasMultimodalAttachments() {
        return Array.isArray(multimodalAttachments) && multimodalAttachments.length > 0;
    }

    function userHasPlaygroundAccess() {
        if (!window.currentUser) {
            return false;
        }
        if (window.currentUser.is_subscribed) {
            return true;
        }
        if (hasMultimodalAttachments() && (window.currentUser.credit_balance_cents || 0) > 0) {
            return true;
        }
        return false;
    }

    function updatePlaygroundAccessState() {
        if (userHasPlaygroundAccess()) {
            $('#playground-play').removeAttr('disabled');
            return;
        }
        $('#playground-play').attr('disabled', true);
        if (window.currentUser) {
            if (hasMultimodalAttachments()) {
                renderPlaygroundAccessMessage({
                    title: 'Credits Required',
                    message: 'Media understanding uses API credits unless you have an active subscription.',
                    primaryLabel: 'Buy Credits',
                    primaryTooltip: 'Purchase one-time API credits for image, audio, and video understanding.',
                    primaryClick: "if (window.showCheckoutDialog) { showCheckoutDialog('credits'); }"
                });
            } else {
                renderPlaygroundAccessMessage({
                    title: 'Subscription Required',
                    message: 'You are signed in, but this playground needs an active subscription.',
                    primaryLabel: 'Subscribe Now',
                    primaryTooltip: 'Open the branded subscription dialog to unlock playground access.',
                    primaryClick: "if (window.subscriptionModal) { window.subscriptionModal.requireSubscription('use the playground'); } else if (window.showCheckoutDialog) { showCheckoutDialog('monthly'); }"
                });
                if (window.subscriptionModal && !window.subscriptionModal.isOpen) {
                    window.subscriptionModal.requireSubscription('use the playground');
                }
            }
        } else {
            renderPlaygroundAccessMessage({
                title: 'Sign In Required',
                message: 'Please sign in to use the playground.',
                primaryLabel: 'Sign In',
                primaryTooltip: 'Open the login modal and stay on this page after authentication.',
                primaryClick: "if (window.showLoginModal) { showLoginModal(); } else { window.location.href='/login'; }",
                secondaryHtml: '<a href="/signup" onclick="if (window.showSignupModal) { showSignupModal(); return false; }" style="display: inline-block; padding: 10px 20px; background: linear-gradient(90deg, #f59e0b, #fbbf24); color: white; text-decoration: none; border-radius: 4px; margin: 5px; border: none; cursor: pointer; transition: all 0.2s ease;">Create account</a>'
            });
        }
    }

    function mapFileToAttachmentType(file) {
        if (!file || !file.type) {
            return null;
        }
        if (file.type.indexOf('image/') === 0) {
            return 'image';
        }
        if (file.type.indexOf('video/') === 0) {
            return 'video';
        }
        if (file.type.indexOf('audio/') === 0) {
            return 'audio';
        }
        return null;
    }

    function renderAttachmentList() {
        var attachmentList = $('#playground-media-list');
        if (!hasMultimodalAttachments()) {
            attachmentList.html('');
            updatePlaygroundAccessState();
            return;
        }
        var html = multimodalAttachments.map(function (attachment, index) {
            return '<div style="display:flex; justify-content:space-between; align-items:center; margin:6px 0; padding:8px 10px; background:#fff; border:1px solid #ece9df; border-radius:8px;">'
                + '<span>' + escapeHtml(attachment.name) + ' <strong style="text-transform:uppercase;">' + escapeHtml(attachment.type) + '</strong></span>'
                + '<button type="button" data-attachment-index="' + index + '" class="mdl-button mdl-js-button remove-media-attachment">Remove</button>'
                + '</div>';
        }).join('');
        attachmentList.html(html);
        updatePlaygroundAccessState();
    }

    async function getSignedUploadUrl(file) {
        var params = new URLSearchParams({
            contentType: file.type || 'application/octet-stream',
            fileName: file.name || 'upload.bin'
        });
        var response = await fetch('/file-upload-get-signed-url-cloudflare?' + params.toString());
        if (!response.ok) {
            throw new Error('Failed to get upload URL');
        }
        return response.json();
    }

    async function uploadAttachmentFile(file) {
        var attachmentType = mapFileToAttachmentType(file);
        if (!attachmentType) {
            throw new Error('Unsupported media type: ' + (file.type || 'unknown'));
        }
        var uploadData = await getSignedUploadUrl(file);
        var uploadResponse = await fetch(uploadData.url, {
            method: 'PUT',
            headers: {
                'Content-Type': file.type || 'application/octet-stream'
            },
            body: file
        });
        if (!uploadResponse.ok) {
            throw new Error('Upload failed for ' + file.name);
        }
        return {
            type: attachmentType,
            name: file.name,
            url: 'https://' + uploadData.bucket_name + '/' + uploadData.object_path,
            mime_type: file.type || 'application/octet-stream'
        };
    }

    async function addAttachmentFiles(fileList) {
        if (!fileList || !fileList.length) {
            return;
        }
        multimodalUploadInFlight = true;
        $('#loading-progress').show();
        try {
            for (var i = 0; i < fileList.length; i++) {
                var uploadedAttachment = await uploadAttachmentFile(fileList[i]);
                multimodalAttachments.push(uploadedAttachment);
            }
            renderAttachmentList();
        } finally {
            multimodalUploadInFlight = false;
            $('#loading-progress').hide();
        }
    }

    async function submitMultimodalPlaygroundRequest() {
        var inferenceBase = (window.fixtures && window.fixtures.inference_server_url) || 'https://api.text-generator.io';
        var text = editor.getValue();
        var content = [];
        if (text) {
            content.push({ type: 'text', text: text });
        }
        multimodalAttachments.forEach(function (attachment) {
            content.push({
                type: attachment.type,
                url: attachment.url,
                mime_type: attachment.mime_type
            });
        });

        var messages = [];
        if (generationSettings.system_message) {
            messages.push({ role: 'system', content: generationSettings.system_message });
        }
        messages.push({ role: 'user', content: content });

        var response = await fetch(inferenceBase + '/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + secret
            },
            body: JSON.stringify({
                model: 'google/gemma-4-26B-A4B-it',
                messages: messages,
                max_tokens: generationSettings.max_length || 512,
                temperature: generationSettings.temperature,
                top_p: generationSettings.top_p,
                top_k: generationSettings.top_k,
                enable_thinking: generationSettings.enable_thinking
            })
        });

        if (!response.ok) {
            throw new Error('Multimodal request failed with status ' + response.status);
        }
        return response.json();
    }

    function showResult(data) {
        data = normalizePlaygroundResponse(data);
        var dataString = JSON.stringify(data, null, 2);
        var htmlEscapedData = escapeHtml(dataString);
        $('#response-results').html(`<pre id="generated-results-code"><code class="language-json">${htmlEscapedData}</code></pre>`);

        if (data[0] && data[0]['generated_text']) {
            let realNewlineData = escapeHtml(data[0]['generated_text']).replace('\n', `
`);
            $('#response-tooltip').html(`${realNewlineData}`);
        }

        // Show thinking content if present
        if (data[0] && data[0]['thinking_content']) {
            $('#thinking-content').text(data[0]['thinking_content']);
            $('#thinking-results').show();
        } else {
            $('#thinking-results').hide();
        }

        hljs.highlightAll();
    }

    function showError(error, status) {
        var dataString = JSON.stringify(error, null, 2);
        $('#response-results').html(`<div style="color: indianred">${status}</div><pre><code class="language-json">${dataString}</code></pre>`);
        hljs.highlightAll();
    }

    function setupSubmitForm() {
        var form = $('#playground-form');
        form.on('submit', function (event) {
            event.preventDefault();
            
            if (multimodalUploadInFlight) {
                return false;
            }

            if (!userHasPlaygroundAccess()) {
                updatePlaygroundAccessState();
                return false;
            }
            
            var text = editor.getValue();
            setTextData(text);

            $('#loading-progress').show();

            $('#playground-play').attr('disabled');
            var requestPromise;
            if (hasMultimodalAttachments()) {
                requestPromise = submitMultimodalPlaygroundRequest();
            } else {
                requestPromise = fetch('https://api.text-generator.io/api/v1/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'secret': secret
                    },
                    body: JSON.stringify(generationSettings)
                }).then(function (response) {
                    if (response.ok) {
                        return response.json();
                    }
                    return response.text().then(function (textError) {
                        showError({ error: textError }, response.status + ' - ' + response.statusText);
                        return [];
                    });
                });
            }

            Promise.resolve(requestPromise).then(function (data) {
                $('#loading-progress').hide();
                updatePlaygroundAccessState();
                showResult(data)
                // if editor hasn't changed write results to codemirror
                if (editor.getValue() === text) {
                    var normalizedData = normalizePlaygroundResponse(data);
                    if (normalizedData[0] && normalizedData[0]['generated_text']) {
                        var generatedText = normalizedData[0]['generated_text'];
                        // Legacy API returns full text; newer paths may return completion-only.
                        var nextValue = generatedText.startsWith(text) ? generatedText : (text + generatedText);

                        var scrollinfo = editor.getScrollInfo();
                        var fromIndex = text.length;
                        editor.setValue(nextValue);

                        var from = editor.posFromIndex(Math.min(fromIndex, nextValue.length));
                        var to = editor.posFromIndex(nextValue.length);
                        if (from.line !== to.line || from.ch !== to.ch) {
                            editor.markText(from, to, { className: 'highlight' });
                        }

                        // scroll to the same position
                        editor.scrollTo(scrollinfo.left, scrollinfo.top);
                    }
                }
            }).catch(function (error) {
                console.log(error);
                showError(error, 500)
                $('#loading-progress').hide();
                updatePlaygroundAccessState();

            })
            return false;
        });

        $(document).on('keydown', function (event) {
            // submit with ctrl enter or cmd enter
            if (event.ctrlKey || event.metaKey) {
                if (event.keyCode === 13) {
                    form.trigger('submit');
                }
            }
        })

        $('#select-stop-sequences').select2({
            tags: true,

            placeholder: 'Multiple stop sequences allowed'
        });

        $('#playground-media').on('change', function (event) {
            addAttachmentFiles(event.target.files).catch(function (error) {
                console.error(error);
                showError({ error: error.message || error }, 500);
            }).finally(function () {
                event.target.value = '';
            });
        });

        $('#playground-media-list').on('click', '.remove-media-attachment', function () {
            var index = parseInt($(this).attr('data-attachment-index'), 10);
            multimodalAttachments.splice(index, 1);
            renderAttachmentList();
        });

        var dropzone = document.getElementById('playground-media-dropzone');
        if (dropzone) {
            ['dragenter', 'dragover'].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function (event) {
                    event.preventDefault();
                    dropzone.style.borderColor = '#f17d34';
                    dropzone.style.background = '#fff3e8';
                });
            });
            ['dragleave', 'drop'].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function (event) {
                    event.preventDefault();
                    dropzone.style.borderColor = '#b7b7c9';
                    dropzone.style.background = '#faf8f5';
                });
            });
            dropzone.addEventListener('drop', function (event) {
                addAttachmentFiles(event.dataTransfer.files).catch(function (error) {
                    console.error(error);
                    showError({ error: error.message || error }, 500);
                });
            });
        }


    }

    function renderPlaygroundAccessMessage(options) {
        var title = options.title;
        var message = options.message;
        var primaryLabel = options.primaryLabel;
        var primaryTooltip = options.primaryTooltip;
        var primaryClick = options.primaryClick || "if (window.showCheckoutDialog) { showCheckoutDialog('monthly'); } else if (window.subscriptionModal) { window.subscriptionModal.show(); }";
        var secondaryHtml = options.secondaryHtml || '';

        $('#response-results').html(`
            <div style="text-align: center; padding: 20px; color: #666;">
                <h3>${title}</h3>
                <p>${message}</p>
                ${secondaryHtml}
                <button id="playground-subscribe-button"
                        type="button"
                        class="mdl-button mdl-js-button mdl-button--raised mdl-button--accent mdl-js-ripple-effect"
                        onclick="${primaryClick}"
                        style="padding: 10px 20px; background: linear-gradient(90deg, #ea580c, #f59e0b); color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px; transition: all 0.2s ease;"
                        onmouseover="this.style.background='linear-gradient(90deg, #c2410c, #d97706)'; this.style.boxShadow='0 4px 15px rgba(234, 88, 12, 0.28)'"
                        onmouseout="this.style.background='linear-gradient(90deg, #ea580c, #f59e0b)'; this.style.boxShadow='none'">${primaryLabel}</button>
                <div id="playground-subscribe-tooltip"
                     class="playground-tooltip mdl-tooltip mdl-tooltip--large"
                     for="playground-subscribe-button"
                     style="white-space: pre">${primaryTooltip}</div>
            </div>
        `);

        if (typeof componentHandler !== 'undefined') {
            componentHandler.upgradeAllRegistered();
        }
    }

    $(document).ready(setupSubmitForm);
    initApp = function () {
        // Check if user is authenticated using new system
        fetch('/api/current-user')
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Not authenticated');
                }
            })
            .then(user => {
                secret = user.secret;
                window.currentUser = user;
                updatePlaygroundAccessState();
            })
            .catch(error => {
                // User is signed out - show upsell instead of redirecting
                console.log('User not authenticated:', error);
                updatePlaygroundAccessState();
            });
    };
    var editor;
    var onceOnly = false;
    window.addEventListener('load', function () {
      if (onceOnly) return;
      onceOnly = true;

      console.log('Playground.js loaded');
      console.log('window.fixtures:', typeof window.fixtures, window.fixtures);
      console.log('$:', typeof $);
      console.log('CodeMirror:', typeof CodeMirror);

      try {
        initApp();
      } catch (e) {
        console.error('Error in initApp:', e);
      }

        setTimeout(function() {
          try {
            var placeholder = "Write here, then click play or (⌘ + Return) to generate."
            if (typeof window.fixtures !== 'undefined' && window.fixtures && !window.fixtures.is_mac) {
              placeholder = "Write here, then click play or (Ctrl + Return) to generate."
            }
            
            var textArea = document.getElementById('playground-text');
            if (!textArea) {
              console.error('playground-text element not found');
              return;
            }
            
            if (typeof CodeMirror === 'undefined') {
              console.error('CodeMirror not available');
              return;
            }
            
            editor = CodeMirror.fromTextArea(textArea, {
                mode: "javascript",
                lineNumbers: true,
                placeholder: placeholder,
                lineWrapping: true
            });
            
            editor.setSize("100%", null);
            editor.on('change', function(editorInstance) {
                var value = editorInstance.getValue();
                setTextData(value);
            });

            editor.save();

            if (typeof $ !== 'undefined') {
              $(document).ready(setupDialog);
            } else {
              console.error('jQuery not available');
            }
          } catch (e) {
            console.error('Error in setTimeout:', e);
          }
        }, 2000);


        $("#open-code-button").click(function (event) {
            try {
                showCode();
                event.preventDefault();
                event.stopPropagation();
                return false;
            } catch (e) {
                console.error('Error in open-code-button click:', e);
            }
        });

    });
