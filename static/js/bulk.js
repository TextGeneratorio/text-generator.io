/** vendored objects to csv
 *
 *
 */


/**
 * Converts an array of objects into a CSV file.
 */
class ObjectsToCsv {
  /**
   * Creates a new instance of the object array to csv converter.
   * @param {object[]} objectArray
   */
  constructor(objectArray) {
    if (!Array.isArray(objectArray)) {
      throw new Error('The input to objects-to-csv must be an array of objects.');
    }

    if (objectArray.length > 0) {
      if (objectArray.some(row => typeof row !== 'object')) {
        throw new Error('The array must contain objects, not other data types.');
      }
    }

    this.data = objectArray;
  }

  /**
   * Saves the CSV file to the specified file.
   * @param {string} filename - The path and filename of the new CSV file.
   * @param {object} options - The options for writing to disk.
   * @param {boolean} [options.append] - Whether to append to file. Default is overwrite (false).
   * @param {boolean} [options.bom] - Append the BOM mark so that Excel shows
   * @param {boolean} [options.allColumns] - Whether to check all items for column names or only the first.  Default is the first.
   * Unicode correctly.
   */
  async toDisk(filename, options) {
    if (!filename) {
      throw new Error('Empty filename when trying to write to disk.');
    }

    let addHeader = false;

    // If the file didn't exist yet or is empty, add the column headers
    // as the first line of the file. Do not add it when we are appending
    // to an existing file.
    const fileNotExists = !fs.existsSync(filename) || fs.statSync(filename).size === 0;
    if (fileNotExists || !options || !options.append) {
      addHeader = true;
    }

    const allColumns = options && options.allColumns
      ? options.allColumns
      : false;

    let data = await this.toString(addHeader, allColumns);
    // Append the BOM mark if requested at the beginning of the file, otherwise
    // Excel won't show Unicode correctly. The actual BOM mark will be EF BB BF,
    // see https://stackoverflow.com/a/27975629/6269864 for details.
    if (options && options.bom && fileNotExists) {
      data = '\ufeff' + data;
    }

    if (options && options.append) {
      return new Promise((resolve, reject) => {
        fs.appendFile(filename, data, 'utf8', (error) => {
          if (error) {
            reject(error);
          } else {
            resolve(data);
          }
        });
      });
    } else {
      return new Promise((resolve, reject) => {
        fs.writeFile(filename, data, 'utf8', (error) => {
          if (error) {
            reject(error);
          } else {
            resolve(data);
          }
        });
      });
    }
  }

  /**
   * Returns the CSV file as string.
   * @param {boolean} header - If false, omit the first row containing the
   * column names.
   * @param {boolean} allColumns - Whether to check all items for column names.
   *   Uses only the first item if false.
   * @returns {Promise<string>}
   */
  async toString(header = true, allColumns = false) {
    return await convert(this.data, header, allColumns);
  }
}

/**
 * Private method to run the actual conversion of array of objects to CSV data.
 * @param {object[]} data
 * @param {boolean} header - Whether the first line should contain column headers.
 * @param {boolean} allColumns - Whether to check all items for column names.
 *   Uses only the first item if false.
 * @returns {string}
 */
async function convert(data, header = true, allColumns = false) {
  if (data.length === 0) {
    return '';
  }

  const columnNames =
    allColumns
      ? [...data
        .reduce((columns, row) => { // check each object to compile a full list of column names
          Object.keys(row).map(rowKey => columns.add(rowKey));
          return columns;
        }, new Set())]
      : Object.keys(data[0]); // just figure out columns from the first item in array

  if (allColumns) {
    columnNames.sort(); // for predictable order of columns
  }

  // This will hold data in the format that `async-csv` can accept, i.e.
  // an array of arrays.
  let csvInput = [];
  if (header) {
    csvInput.push(columnNames);
  }

  // Add all other rows:
  csvInput.push(
    ...data.map(row => columnNames.map(column => row[column])),
  );

  return await csv.stringify(csvInput);
}

function displayTextGenerationCode() {
    $('#code-snippet').show();
    $('#code-snippet-embed').hide();
}

function displayEmbedCode() {
    $('#code-snippet').hide();
    $('#code-snippet-embed').show();
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
    history.replaceState(null, null, '/bulk-text-generator?' + urlParams.toString());


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

    generationSettings = {
        "text": params.text,
        "number_of_results": parseInt(params.number_of_results),
        "max_length": parseInt(params.max_length),
        "max_sentences": parseInt(params.max_sentences),
        "min_probability": parseFloat(params.min_probability),
        "stop_sequences": stopSequencesArray,
        "model": params.model || 'best',
        "top_p": parseFloat(params.top_p),
        "top_k": parseInt(params.top_k),
        "temperature": parseFloat(params.temperature),
        "repetition_penalty": parseFloat(params.repetition_penalty),
        "seed": parseInt(params.seed),
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
    },
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
    $('#select-model').val(preset.model).change();

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
var setModel = function (value) {
  var value = $('#setModelDropdown').select2('data');
  if(value.length > 0) {
    value = value[0].text;
  } else {
    value = 'best';
  }
  generationSettings['model'] = value.toLowerCase();
  setModel(value);
}
var setTopP = function (value) {
    var value = parseFloat(value);
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
var showCode = function () {

    var generationSettingsFormatted = JSON.stringify(generationSettings, null, 4);
    $('#code-snippet').html(`import requests

headers = {"secret": "${secret}"}

data = ${generationSettingsFormatted}

res = requests.post(
   "https://api.text-generator.io/api/v1/generate",
   json=data,
   headers=headers
)`);
    $('#code-snippet-embed').html(`import requests

headers = {"secret": "${secret}"}

data = {
    "text": ${JSON.stringify(generationSettings.text, null, 4) || "\"Test text here\""}
}
res = requests.post(
   "https://api.text-generator.io/api/v1/feature-extraction",
   json=data,
   headers=headers
)`);
    hljs.highlightAll();
    var dialog = document.querySelector('dialog');
    dialog.showModal();
    return false;
}

function setGenerationSettingsUI(review) {
    setNumberOfResults(review['number_of_results']);
    setMaxLength(review['max_length']);
    setMaxSentences(review['max_sentences']);
    setMinProbability(review['min_probability']);
    setStopSequences(review['stop_sequences']);
    setModel(review['model'])
    setTopP(review['top_p']);
    setTopK(review['top_k']);
    setTemperature(review['temperature']);
    setRepetitionPenalty(review['repetition_penalty']);
    setSeed(review['seed']);
}

function setupDialog() {
    var dialog = document.querySelector('dialog');
    if (!dialog.showModal) {
        return
        //todo polyfill>?
        //dialogPolyfill.registerDialog(dialog);
    }
    dialog.querySelector('.close').addEventListener('click', function () {
        dialog.close();
    });
    // default to Review Classification
    setupFromUrl();
}

function showError(error, status) {
    var dataString = JSON.stringify(error, null, 2);
    $('#response-results').html(`<div style="color: indianred">${status}</div><pre><code class="language-json">${dataString}</code></pre>`);
    hljs.highlightAll();
}

async function makeRequestChain(generateSettingsList) {

    const results = [];
    for (const generateSettings of generateSettingsList) {
        let response = await fetch('https://api.text-generator.io/api/v1/generate', {
                //requestChain = fetch('https://localhost:3031/api/v1/generate-bulk', {
                method: 'POST',
                headers: {
                    'Content-Type':
                        'application/json',
                    'secret':
                    secret
                }
                ,
                body: JSON.stringify(generateSettings)
            }
        );
        if (!response.ok) {
            response = await fetch('https://api.text-generator.io/api/v1/generate', {
                    //requestChain = fetch('https://localhost:3031/api/v1/generate-bulk', {
                    method: 'POST',
                    headers: {
                        'Content-Type':
                            'application/json',
                        'secret':
                        secret
                    }
                    ,
                    body: JSON.stringify(generateSettings)
                }
            );
            if (!response.ok) {
                showError(response.text(), response.status);
            }
        }
        results.push(await response.json());
    }
    $('#loading-progress').hide();

    $('#playground-play').removeAttr('disabled');
    return results;
}

async function submitForm() {
    var generateSettingsList = csvUploaded;
    if (!generateSettingsList) {
        alert('Upload a csv with a "text" column (and other generate settings)');
        return;
    }

    $('#loading-progress').show();
    $('#playground-play').attr('disabled');

    var results = await makeRequestChain(generateSettingsList);
    // encode in csv download
    // var csvData = [];
    // results.map(function (result) {
    //     if (result) {
    //         result.forEach(function (item) {
    //             csvData.push(`"${item['generated_text'].replace('"', '""')}",${item['stop_reason']}`);
    //         });
    //     }
    // });
    // csvData = csvData.join('\n');
    // csvData = `"generated_text","stop_reason"\n${csvData}`;
    var flatResults = [];
    results.map(function (result) {
        if (result) {
            result.forEach(function (item) {
                flatResults.push(item);
            });
        }
    });
    // const csv = new ObjectsToCsv(flatResults);

  // Return the CSV file as string:
    let csvData = Papa.unparse(flatResults);
    var blob = new Blob([csvData], {type: "text/csv"});
    var href = window.URL.createObjectURL(blob)
    $('#download-csv').attr('href', href);
    $('#download-csv').removeAttr('disabled');
}

function setupSubmitForm() {
    var form = $('#playground-form');
    form.on('submit', function (event) {
        event.preventDefault();
        event.stopPropagation();
        submitForm();
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
    })
    $('#select-model').select2({
        // tags: true,
        multiple: false,
        placeholder: 'Best'
    })
}

initApp = function () {
    firebase.auth().onAuthStateChanged(function (user) {
        if (user) {
            // User is signed in.
            var displayName = user.displayName;
            var email = user.email;
            var emailVerified = user.emailVerified;
            var photoURL = user.photoURL;
            var uid = user.uid;
            var phoneNumber = user.phoneNumber;
            var providerData = user.providerData;
            getUser(user, function (data) {

                secret = data['secret'];
                // enable submit form
                $('#playground-play').removeAttr('disabled');


            })
        } else {
            // User is signed out.
            location.href = '/login'
        }
    }, function (error) {
        console.log(error);
    });
};
var editor;


function csvToArray(text) {
    let p = '', row = [''], ret = [row], i = 0, r = 0, s = !0, l;
    for (l of text) {
        if ('"' === l) {
            if (s && l === p) row[i] += l;
            s = !s;
        } else if (',' === l && s) l = row[++i] = '';
        else if ('\n' === l && s) {
            if ('\r' === p) row[i] = row[i].slice(0, -1);
            row = ret[++r] = [l = ''];
            i = 0;
        } else row[i] += l;
        p = l;
    }
    return ret;
}

/**
 * takes a csv 2d array and returns arrays of json where the header is the key and the value is the value
 * @param csv 2d array of csv data, first line is the header
 * @returns {*[]}
 */
function csvToJSON(csv) {


    var csvArray = csvToArray(csv);

    var jsonArray = [];
    var header = csvArray[0];
    var values = csvArray.slice(1);
    for (var i = 0; i < values.length; i++) {
        var json = {};
        for (var j = 0; j < header.length; j++) {
            json[header[j]] = values[i][j];
        }
        jsonArray.push(json);
    }
    return jsonArray;
}

function validateCSV(csv_contents) {
    var isValid = true;
    let json = []
    try {
        json = csvToJSON(csv_contents);
    } catch (e) {
        console.log(error);
        return "failed to process csv, use coma seperations";
    }
    if (json.length == 0) {
        return "No items found in csv";
    }
    // remove all empty elements
    json = json.filter(function (item) {
        return Object.keys(item).length > 0 && item['text'];
    });

    for (let i = 0; i < json.length; i++) {
        if (!json[i]['text']) {
            continue;
        }
        if (json[i]['min_probability']) {
            // should be a float
            if (isNaN(json[i]['min_probability'])) {
                return "min_probability should be a float";
            }
            json[i]['min_probability'] = parseFloat(json[i]['min_probability']);
        } else {
            json[i]['min_probability'] = generationSettings.min_probability;
        }
        if (json[i]['temperature']) {
            // should be a float
            if (isNaN(json[i]['temperature'])) {
                return "temperature should be a float";
            }
            json[i]['temperature'] = parseFloat(json[i]['temperature']);
        } else {
            json[i]['temperature'] = generationSettings.temperature;
        }
        if (json[i]['top_p']) {
            // should be a float
            if (isNaN(json[i]['top_p'])) {
                return "top_p should be a float";
            }
            json[i]['top_p'] = parseFloat(json[i]['top_p']);
        } else {
            json[i]['top_p'] = generationSettings.top_p;
        }
        if (json[i]['repetition_penalty']) {
            // should be a float
            if (isNaN(json[i]['repetition_penalty'])) {
                return "repetition_penalty should be a float";
            }
            json[i]['repetition_penalty'] = parseFloat(json[i]['repetition_penalty']);
        } else {
            json[i]['repetition_penalty'] = generationSettings.repetition_penalty;
        }
        if (json[i]['number_of_results']) {
            // should be a float
            if (isNaN(json[i]['number_of_results'])) {
                return "number_of_results should be an integer";
            }
            json[i]['number_of_results'] = parseInt(json[i]['number_of_results']);
        } else {
            json[i]['number_of_results'] = generationSettings.number_of_results;
        }
        if (json[i]['max_sentences']) {
            // should be a float
            if (isNaN(json[i]['max_sentences'])) {
                return "max_sentences should be an integer";
            }
            json[i]['max_sentences'] = parseInt(json[i]['max_sentences']);
        } else {
            json[i]['max_sentences'] = generationSettings.max_sentences;
        }
        if (json[i]['max_length']) {
            // should be a float
            if (isNaN(json[i]['max_length'])) {
                return "max_length should be an integer";
            }
            json[i]['max_length'] = parseInt(json[i]['max_length']);
        } else {
            json[i]['max_length'] = generationSettings.max_length;
        }
        if (json[i]['seed']) {
            // should be a float
            if (isNaN(json[i]['seed'])) {
                return "seed should be an integer";
            }
            json[i]['seed'] = parseInt(json[i]['seed']);
        } else {
            json[i]['seed'] = generationSettings.seed;
        }
        if (json[i]['top_k']) {
            // should be a float
            if (isNaN(json[i]['top_k'])) {
                return "top_k should be an integer";
            }
            json[i]['top_k'] = parseInt(json[i]['top_k']);
        } else {
            json[i]['top_k'] = generationSettings.top_k;
        }
        if (json[i]['stop_sequences']) {
            json[i]['stop_sequences'] = json[i]['stop_sequences'].split(
                ",")
        } else {
            json[i]['stop_sequences'] = generationSettings.stop_sequences || [];
        }
        if (json[i]['model']) {
            json[i]['model'] = json[i]['model'].toLowerCase();
        }
        else {
            json[i]['model'] = generationSettings.model || 'best';
        }

    }
    return json;
}

function decodedCSV(file) {
    // decode base64 data in the form "data:text/csv;base64,..."
    return atob(file.split(",")[1]);
}

window.addEventListener('load', function () {
    initApp()

    $(document).ready(setupDialog);
    $(document).ready(setupSubmitForm);

    $("#open-code-button").click(function (event) {
        showCode();
        event.preventDefault();
        event.stopPropagation();
        return false;
    });
    let dropArea = document.getElementById("drop-area")

// Prevent default drag behaviors
    ;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false)
        document.body.addEventListener(eventName, preventDefaults, false)
    })

// Highlight drop area when item is dragged over it
    ;['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false)
    })

    ;['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false)
    })

// Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false)

    function preventDefaults(e) {
        e.preventDefault()
        e.stopPropagation()
    }

    function highlight(e) {
        dropArea.classList.add('highlight')
    }

    function unhighlight(e) {
        dropArea.classList.remove('active')
    }

    function handleDrop(e) {
        var dt = e.dataTransfer
        var files = dt.files

        handleFiles(files)
    }

    let uploadProgress = []

    function initializeProgress(numFiles) {
    }

    function updateProgress(fileNumber, percent) {
    }
    $('#fileElem').change(function(ev) {
        // var dt = e.dataTransfer
        // var files = dt.files

        handleFiles($('#fileElem')[0].files)
    })

    function handleFiles(files) {
        files = [...files]
        initializeProgress(files.length)
        files.forEach(previewFile)
    }

    function previewFile(file) {
        let reader = new FileReader();
        reader.readAsDataURL(file)
        reader.onloadend = function () {
            let csv_contents = decodedCSV(reader.result);
            let csvResult = validateCSV(csv_contents);
            if (typeof csvResult === 'string') {
                alert(csvResult);
                return;
            }
            $('#upload-success-message').html("Validated CSV file. You can now run generation. " + csvResult.length + " results will be generated.");
            csvUploaded = csvResult;
        }
    }
});
var csvUploaded;

