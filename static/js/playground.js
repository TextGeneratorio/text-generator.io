
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
            "seed": 0
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
        value = $('#select-model').val();
        $('#model-tooltip').html(`Model: ${value}`);
        generationSettings['model'] = value
        setUrl(generationSettings)
    }

    var showCode = function () {

        var generationSettingsFormatted = JSON.stringify(generationSettings, null, 4);
        var generationSettingsCurlFormatted = JSON.stringify(generationSettings, null, 0);
        $('#code-snippet-py').html(`import requests

headers = {"secret": "${secret}"}

data = ${generationSettingsFormatted}

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
        var dialog = document.querySelector('dialog');
        dialog.close();
        dialog.showModal();
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

    function showResult(data) {
        var dataString = JSON.stringify(data, null, 2);
        var htmlEscapedData = escapeHtml(dataString);
        $('#response-results').html(`<pre id="generated-results-code"><code class="language-json">${htmlEscapedData}</code></pre>`);

        if (data[0] && data[0]['generated_text']) {
            let realNewlineData = escapeHtml(data[0]['generated_text']).replace('\n', `
`);
            $('#response-tooltip').html(`${realNewlineData}`);
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
            
            // Check subscription before submitting
            if (!window.currentUser || !window.currentUser.is_subscribed) {
                subscriptionModal.requireSubscription('use the playground');
                return false;
            }
            
            var text = editor.getValue();
            setTextData(text);

            $('#loading-progress').show();

            $('#playground-play').attr('disabled');
            fetch('https://api.text-generator.io/api/v1/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'secret': secret
                },
                body: JSON.stringify(generationSettings)
            }).then(function (response) {
                $('#loading-progress').hide();

                $('#playground-play').removeAttr('disabled');

                if (response.ok) {
                    return response.json();
                } else {
                    showError(response.text(), response.status + ' - ' + response.statusText);
                }
            }).then(function (data) {
                showResult(data)
                // if editor hasn't changed write results to codemirror
                if (editor.getValue() === text) {
                    if (data[0] && data[0]['generated_text']) {
                        // highlight the new text with markRange
                        var scrollinfo = editor.getScrollInfo();
                        var from = { line: 0, ch: 0 };
                        from.line = editor.lineCount() - 1;
                        from.ch = editor.getLine(from.line).length;

                        editor.setValue(data[0]['generated_text']);

                        var to = { line: 0, ch: 0 };
                        var newText = data[0]['generated_text'];
                        var newLines = newText.split('\n');
                        var newLineCount = newLines.length;
                        var newLineLength = newLines[newLineCount - 1].length;
                        to.line = newLineCount - 1;
                        to.ch = newLineLength;
                        editor.markText(from, to, { className: 'highlight' });

                        // scroll to the same position
                        editor.scrollTo(scrollinfo.left, scrollinfo.top);
                    }
                }
            }).catch(function (error) {
                console.log(error);
                showError(error, 500)
                $('#loading-progress').hide();

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
                // enable submit form only if user is subscribed
                if (user.is_subscribed) {
                    $('#playground-play').removeAttr('disabled');
                } else {
                    $('#playground-play').attr('disabled', true);
                    // Show subscription message
                    $('#response-results').html(`
                        <div style="text-align: center; padding: 20px; color: #666;">
                            <h3>Premium Feature</h3>
                            <p>The playground requires an active subscription to use.</p>
                            <button onclick="subscriptionModal.show()" style="padding: 10px 20px; background: linear-gradient(90deg, #d79f2a, #d34675); color: white; border: none; border-radius: 4px; cursor: pointer; transition: all 0.2s ease;" onmouseover="this.style.background='linear-gradient(90deg, #c48d24, #c23e67)'; this.style.boxShadow='0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15)'" onmouseout="this.style.background='linear-gradient(90deg, #d79f2a, #d34675)'; this.style.boxShadow='none'">Subscribe Now</button>
                        </div>
                    `);
                }
            })
            .catch(error => {
                // User is signed out - show upsell instead of redirecting
                console.log('User not authenticated:', error);
                $('#playground-play').attr('disabled', true);
                $('#response-results').html(`
                    <div style="text-align: center; padding: 20px; color: #666;">
                        <h3>Sign In Required</h3>
                        <p>Please sign in to use the playground.</p>
                        <a href="/login" style="display: inline-block; padding: 10px 20px; background: linear-gradient(90deg, #d79f2a, #d34675); color: white; text-decoration: none; border-radius: 4px; margin: 5px; border: none; cursor: pointer; transition: all 0.2s ease;">Sign In</a>
                        <button onclick="subscriptionModal.show()" style="padding: 10px 20px; background: linear-gradient(90deg, #d79f2a, #d34675); color: white; border: none; border-radius: 4px; cursor: pointer; margin: 5px; transition: all 0.2s ease;" onmouseover="this.style.background='linear-gradient(90deg, #c48d24, #c23e67)'; this.style.boxShadow='0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15)'" onmouseout="this.style.background='linear-gradient(90deg, #d79f2a, #d34675)'; this.style.boxShadow='none'">Get Premium Access</button>
                    </div>
                `);
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
