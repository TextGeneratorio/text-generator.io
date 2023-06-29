// var api_base_url = "https://text-generator.io/api/v1/generate"
function randomString(length) {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for (var i = 0; i < length; i++)
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    return text;
}
var api_base_url = "https://api.text-generator.io/api/v1/generate"
$(function () {
    "use strict";
    window.questionsgame = {};
    var self = window.questionsgame;


    self.Game = function (input) {

        var gameState = {
            numQuestions: 0,
            input: input,
            originalInput: input,
            extra_lines: '',
            moves: 0,
            repetition_penalty: 1.4,
        }

        $('.form-horizontal').on('submit', function (event) {
            event.preventDefault();
            event.stopPropagation();

            //get text of questions form
            let sentText = $('.question-text').val();
            $('.question-text').val('');
            $('.question-text').focus();

            // fetch json from text-generator endpoint
            gameState.input += `
John: ${sentText}
Adam:`;
            // loading spinner
            $('.chat-log').append(`<div class="chat-log__item chat-log__item--own">
                            <div class="chat-log__message">
                                ${sentText}
                            </div>
                        </div>
                        <div class="chat-log__item loading-chat-bar">
                            <div id="loading-bubble">
                                <div class="spinner">
                                    <div class="bounce1"></div>
                                    <div class="bounce2"></div>
                                    <div class="bounce3"></div>
                                </div>
                            </div>
                        </div>`);

            $(document).scrollTop($(document).height());

            function fetch_result(retries) {
                gameState.input = gameState.input.replace(/\n+/g, '\n');
                var data = {
                    "text": gameState.input,
                    "number_of_results": 1,
                    "max_length": 100,
                    "min_length": 1,
                    "max_sentences": 1,
                    "min_probability": 0,
                    "stop_sequences": ["John:", "Adam:", "john:", "adam:", ":", "Bob:", "George:"],
                    "top_p": .93,
                    "top_k": 50,
                    "temperature": 1.0,
                    "repetition_penalty": gameState.repetition_penalty + Math.random() * .3,
                    "seed": 0
                }
                fetch(api_base_url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        "X-Rapid-API-Key": "YHWEFVNWHXIWNGVSH"
                    },
                    body: JSON.stringify(data),
                })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Success:', data);
                        let generatedText = data[0]["generated_text"];
                        var lastLocation = generatedText.lastIndexOf("Adam:");
                        let prediction = generatedText.substr(lastLocation + 5).trim();
                        if (!prediction || prediction.length === 0) {
                            if (retries === 0) {
                                return fetch_result(1);
                            }
                            prediction = Math.random() > 0.5 ? "Yep" : "Nope";
                        }
                        gameState.input = generatedText;
                        if (prediction === gameState.lastGeneratedText) {
                            gameState.input = gameState.originalInput + `
John: ${sentText}
Adam:`;                     if (retries === 0) {
                                return fetch_result(1);
                            }
                        }
                        gameState.lastGeneratedText = prediction;

                        //tried instead of appending adams answers we suppress them to avoid looping
                        // gameState.input = gameState.input.replace("\nAdam:", "");
                        // gameState.input = gameState.input.replace("\nJohn:", "");
                        // append prediction
                        $('.loading-chat-bar').remove();
                        $('.chat-log').append(`<div class="chat-log__item">
                            <h3 class="chat-log__author">Adam Bottington</h3>
                            <div class="chat-log__message"><span class="typer" id="typer-${randomString(10)}"
                                                                  data-words="${prediction}" data-delay="50" data-delim="-------"
                                                                  data-loop="1"
                            ></span></div>
                        </div>`);
                        $(document).scrollTop($(document).height());
                        // setup typer again
                        TyperSetup();
                    })
                    .catch((error) => {
                        //todo retry forever
                        console.error('Error:', error);
                    });
            }

            fetch_result(0);
            return false;
        })

        function construct() {


        }

        gameState.getNewPrompt = function () {
            gameState.numQuestions++;
        }

        gameState.EndHandler = function () {
            var endSelf = {};
            endSelf.render = function (target) {
                endSelf.$target = $(target);
                if (gameState.moves) {
                    endSelf.$target.html('<p>Moves: ' + endSelf.moves + '</p>');
                } else {
                    endSelf.$target.html('<p>Time: <span class="gameon-clock"></span></p>');
                }
            };
            endSelf.setMoves = function (moves) {
                endSelf.moves = moves;
                // unlimited moves/dont end the game
                // if (moves <= 0) {
                //     //todo settimeout so they can watch successanimation
                //     endSelf.gameOver();
                //     return;
                // }
                endSelf.render(endSelf.$target);
            };

            endSelf.turnEnd = function ($words) {
                for (var i = 0; i < $words.length; i++) {
                    var $word = $words.eq(i);
                    if ($word.data('index') != gameState.correct_ordering[i]) {
                        return false;
                    }
                }
                //show done

                //gameState.destruct();
                gameon.getUser(function (user) {
                    if (user.levels_unlocked < gameState.id) {
                        user.saveLevelsUnlocked(gameState.id);
                    }
                    APP.doneLevel(gameState);
                });
            };

            return endSelf;
        };


        gameState.render = function (target) {
            gameState.$target = $(target);
            gameState.$target.html(gameState.$html);
        };

        construct();
        return gameState;
    };
    const colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white'];
    const topics = ['animals', "mythology", "celebrities", "sports", "geography", "food", "science", "history", "music", "art", "computers", "books"];

    // pick random
    const colorProb = .1;
    const topicProb = .9;
    let prompt = ""
    if (Math.random() < colorProb) {
        prompt += colors[parseInt(Math.random() * colors.length)];
    }
    if (Math.random() < topicProb) {
        prompt += " " + topics[parseInt(Math.random() * topics.length)];
    }

    // prompt = "thinking about something " + prompt;
    //Adam is polite happy funny, i can respond yes no or however i feel like
    let input =
        `Adam: Lets play a funny game, i think of something ${prompt}, you have to guess what it is. You can guess as many times as you want. if i say "your correct!" then you win
`
    self.game = new self.Game(input);
    self.game.render($('#gameon-game'));

    return self;
});
