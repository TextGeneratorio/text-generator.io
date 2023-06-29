var GameOnUser = function (userJSON) {
    if (!userJSON) {
        userJSON = {};
    }
    if (typeof userJSON.scores == 'undefined') {
        userJSON.scores = [];
    }
    if (typeof userJSON.levels_unlocked == 'undefined') {
        userJSON.levels_unlocked = 0;
    }

    if (typeof userJSON.difficulties_unlocked == 'undefined') {
        userJSON.difficulties_unlocked = 0;
    }

    userJSON.saveScore = function (game_mode, score, callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/savescore",
            "data": {game_mode: game_mode, score: score},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.scores.push({'game_mode': game_mode, 'score': score});
        reorderScores();
    };
    userJSON.deleteAllScores = function (callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/deleteallscores",
            "data": {},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.scores = [];
    };

    var reorderScores = function () {
        userJSON.scores.sort(function (a, b) {
            return a.game_mode - b.game_mode;
        });
    };
    reorderScores();

    userJSON.getHighScores = function () {
        var highScores = [];
        var scores = userJSON.scores;

        for (var groupNum = 0; groupNum < scores.length;) {

            var highScore = scores[groupNum].score;
            var highScoreIdx = groupNum;

            var groupLength = 1;
            //find max high score in group
            for (var i = groupNum + 1; i < scores.length && scores[i].game_mode === scores[i - 1].game_mode; i++) {
                if (highScore < scores[i].score) {
                    highScore = scores[i].score;
                    highScoreIdx = i;
                }
                groupLength++;
            }
            highScores.push(scores[highScoreIdx]);
            groupNum += groupLength;
        }

        return highScores;
    };

    userJSON.saveAchievement = function (achievementNumber, callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/saveachievement",
            "data": {type: achievementNumber},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.achievements.push({type: achievementNumber})
    };

    userJSON.saveVolume = function (volume, callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/savevolume",
            "data": {volume: volume},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.volume = volume
    };

    userJSON.saveMute = function (mute, callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/savemute",
            "data": {mute: mute},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.mute = mute

    };

    userJSON.saveLevelsUnlocked = function (levelsUnlocked, callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/savelevelsunlocked",
            "data": {levels_unlocked: levelsUnlocked},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.levels_unlocked = levelsUnlocked
    };

    userJSON.saveDifficultiesUnlocked = function (difficultiesUnlocked, callback) {
        if (typeof callback == 'undefined') {
            callback = function (data) {
            }
        }
        $.ajax({
            "url": "/gameon/savedifficultiesunlocked",
            "data": {difficulties_unlocked: difficultiesUnlocked},
            "success": function (data) {
                callback(data)
            },
            "type": "GET",
            "cache": false,
            "error": function (xhr, error, thrown) {
                if (error == "parsererror") {
                }
            }
        });
        userJSON.difficulties_unlocked = difficultiesUnlocked
    };


    return userJSON;
};
window.gameon = new (function () {
    "use strict";
    var self = window.gameon || {};

    self.getUser = function (callback) {
        if (self.user) {
            callback(self.user);
        }
        else {

            $.ajax({
                "url": "/gameon/getuser",
                "data": {},
                "success": function (user) {
                    self.user = GameOnUser(user);
                    callback(self.user);
                },
                "type": "GET",
                "cache": false,
                "error": function (xhr, error, thrown) {
                    if (error == "parsererror") {
                    }
                }
            });
        }
    };

    // ========== SOUND ================

    soundManager.setup({
        // where to find the SWF files, if needed
        url: '/gameon/static/js/lib/soundmanager/swf',
        onready: function () {
            // SM2 has loaded, API ready to use e.g., createSound() etc.
        },
        ontimeout: function () {
            // Uh-oh. No HTML5 support, SWF missing, Flash blocked or other issue
        }

    });

    self.loadSound = function (name, url) {
        soundManager.onready(function () {
            soundManager.createSound({
                id: name,
                url: url
            });
        });
    };

    self.loadSound("doublepoints", '/gameon/static/music/doublepoints.m4a');

    soundManager.onready(function () {
        var sound = soundManager.getSoundById("doublepoints");
        if (sound.isHTML5) {
            var html5audio = new Audio();
            html5audio.volume = 0.34;
            if (html5audio.volume != 0.34) {
                self.noAudioChange = true;
            }
        }

    });

    self.getSoundPosition = function (name) {
        return soundManager.getSoundById(name).position;
    };

    self.isPlaying = function (name) {
        return soundManager.getSoundById(name).playState == 1;
    };
    self.playSound = function (name, callback) {
        if (typeof callback == 'undefined') {
            callback = function () {
            };
        }
        soundManager.onready(function () {
            soundManager.play(name, {
                onfinish: function () {
                    callback();
                }
            });
        });
    };

    self.pauseSound = function (name) {
        soundManager.onready(function () {
            soundManager.pause(name);
        });
    };

    self.pauseAll = soundManager.pauseAll;
    self.resumeAll = soundManager.resumeAll;

    /**
     * @param volume 0 to 1 global volume
     */
    self.setVolume = function (volume) {
        volume = volume * 100;
        $.each(soundManager.sounds, function (name, sound) {
            sound.setVolume(volume);
        });
    };

    function _loopSound(sound) {
        sound.play({
            onfinish: function () {
                _loopSound(sound);
            }
        });
    }

    self.loopSound = function (name) {
        soundManager.onready(function () {
            var sound = soundManager.getSoundById(name);
            _loopSound(sound);
//            sound.play({loops:999999});
        });
    };
    self.loopSoundAtPosition = function (name, position) {
        soundManager.onready(function () {
            var sound = soundManager.getSoundById(name);

            soundManager.play(name, {
                position: position,
                onfinish: function () {
                    _loopSound(sound);
                }
            });
        });
    };


    self.mute = function () {
        soundManager.mute();
        self.getUser(function (user) {
            user.saveMute(1);
        });
    };

    self.unmute = function () {
        soundManager.unmute();
        self.getUser(function (user) {
            user.saveMute(0);
        });
    };
    self.muteSound = function (name) {
        soundManager.mute(name);
    };

    self.unmuteSound = function (name) {
        soundManager.unmute(name);
    };

    //TODO TEST clicks
    self.muteClick = function () {
        $('.gameon-volume__unmute').show();
        $('.gameon-volume__mute').hide();
        self.mute();
    };
    self.unmuteClick = function () {
        $('.gameon-volume__unmute').hide();
        $('.gameon-volume__mute').show();
        self.unmute();
    };

    self.renderVolumeTo = function (target) {
        var $target = $(target);
        var $volumeControl = $('.gameon-volume-template .gameon-volume').detach();
        if (self.noAudioChange) {
            return;
        }
        $volumeControl.appendTo($target);

        $target.bind('destroyed', function () {
            $target.find('.gameon-volume').detach().appendTo('.gameon-volume-template');
        });
    };


    self.getUser(function (user) {
        //render volume control
        $(document).ready(function () {
            var slider = $(".gameon-volume [data-slider]");
            slider.simpleSlider("setRatio", user.volume);
            if (user.mute) {
                $('.gameon-volume__unmute').show();
                self.mute();
            }
            else {
                $('.gameon-volume__mute').show();
            }

            slider
                .bind("slider:ready slider:changed", function (event, data) {
                    self.setVolume(data.ratio);
                    self.getUser(function (user) {
                        user.saveVolume(data.ratio);
                    });

                });
        });
    });


    // ===================       Clock       ===============================

    self.clock = function (gameOver, startSeconds) {
        var self = {};

        self.init = function (gameOver, startSeconds) {
            if (!startSeconds) {
                self.startSeconds = 5 * 60;
            }
            else {
                self.startSeconds = startSeconds;
            }
            self.reset();
            self.gameOver = gameOver;
            return self;
        };
        self.gameOver = function () {
        };
        self.startSeconds = 5 * 60;
        self.started = false;

        self.reset = function () {
            self.seconds = self.startSeconds;
            self.started = false;
        };

        self.start = function () {
            self.started = true;
        };
        self.unpause = self.start;
        self.pause = function () {
            self.started = false;
        };

        self.tick = function () {

        };

        self.getTime = function () {
            return self._formattedTime;
        };
        self.setTime = function (seconds) {
            self.seconds = seconds;
            self._updateFormattedTime();
        };

        self._updateFormattedTime = function () {
            var separator = ':';
            if (self.seconds % 60 <= 9) {
                separator = ':0';
            }
            self._formattedTime = Math.floor(self.seconds / 60) + separator + self.seconds % 60;
        };
        self.setTime(self.startSeconds);

        setInterval(function () {
            if (self.started) {
                self.setTime(self.seconds - 1);
                self._updateFormattedTime();
                self.tick();
                $('.gameon-clock').html(self.getTime());
                if (self.seconds <= 0) {
                    self.reset();
                    self.gameOver();
                }
            }
        }, 1000);

        return self.init(gameOver, startSeconds);
    };

    // =====================       Board            ===========================
    var numBoards = 0;

    /**
     * tiles MUST have the functions click(), reRender() and render()
     * @param width
     * @param height
     */
    self.boards = {};
    self.cleanBoards = function () {
        self.boards = {};
        numBoards = 0;
    };

    self.Board = function (width, height, tiles) {
        var boardSelf = this;

        function construct(width, height, tiles) {
            numBoards++;
            boardSelf.id = numBoards;
            boardSelf.name = 'board' + numBoards;
            //TODO need to delete/garbage collect these boards
            self.boards[boardSelf.name] = boardSelf;

            boardSelf.width = width;
            boardSelf.height = height;
            boardSelf.tiles = tiles;
            for (var i = 0; i < boardSelf.tiles.length; i++) {
                var currTile = boardSelf.tiles[i];

                var x = boardSelf.getX(i);
                var y = boardSelf.getY(i);

                boardSelf.newTile(y, x, currTile);
            }
        }

        boardSelf.isInBoard = function (y, x) {
            return y >= 0 && x >= 0 && y < boardSelf.height && x < boardSelf.width;
        };

        boardSelf.newTile = function (y, x, tile) {
            tile.yPos = y;
            tile.xPos = x;

            if (!tile.canPassThrough) {
                tile.canPassThrough = false;
            }
            tile.toString = function () {
                return tile.yPos + '-' + tile.xPos;
            };
            tile.tileRender = function (extraCss) {
                var renderedData;
                if (typeof this['render'] === 'function') {
                    renderedData = $(this.render());
                }
                else {
                    renderedData = $('<div></div>');
                }
                renderedData.on('mousedown touchstart', function (evt) {
                    evt.preventDefault();
                    evt.stopPropagation();
                    gameon.boards[boardSelf.name].click(renderedData);
                });

                renderedData.attr('data-yx', boardSelf.name + '-' + this.yPos + '-' + this.xPos);
                renderedData.css({position: 'relative'});
                if (typeof extraCss == "object") {
                    renderedData.css(extraCss);
                }
                return renderedData;
            };
            tile.reRender = function () {
                var renderedTile = boardSelf.getRenderedTile(this.yPos, this.xPos);
                var container = renderedTile.parent();
                container.html(tile.tileRender());
            };

            tile.isTile = function () {
                return typeof this['render'] === 'function';
            };

            tile.getRenderedTile = function () {
                return boardSelf.getRenderedTile(this.yPos, this.xPos)
            };
            tile.getRenderedCell = function () {
                return boardSelf.getRenderedCell(this.yPos, this.xPos)
            };
        };

        boardSelf.getY = function (i) {
            return Math.floor(i / boardSelf.width);
        };
        boardSelf.getX = function (i) {
            return i % boardSelf.width;
        };

        boardSelf.getTile = function (y, x) {
            if ($.isArray(y)) {
                x = y[1];
                y = y[0];
            }
            return boardSelf.tiles[y * boardSelf.width + x];
        };
        boardSelf.setTile = function (y, x, tile) {
            if ($.isArray(y)) {
                tile = x;
                x = y[1];
                y = y[0];
            }
            boardSelf.newTile(y, x, tile);
            boardSelf.tiles[y * boardSelf.width + x] = tile;
        };

        boardSelf.swapTiles = function (a1, a2, a3, a4) {
            var y1, x1, y2, x2;
            if ($.isArray(a1)) {
                y1 = a1[0];
                x1 = a1[1];
            }
            else if (typeof a1 == 'object') {
                y1 = a1.yPos;
                x1 = a1.xPos;
            }
            else {
                y1 = a1;
                x1 = a2;
            }

            if ($.isArray(a2)) {
                y2 = a2[0];
                x2 = a2[1];
            }
            else if (typeof a2 == 'object') {
                y2 = a2.yPos;
                x2 = a2.xPos;
            }
            else {
                y2 = a3;
                x2 = a4;
            }
            var tmp = boardSelf.getTile(y1, x1);
            boardSelf.setTile(y1, x1, boardSelf.getTile(y2, x2));
            boardSelf.setTile(y2, x2, tmp);
        };

        boardSelf.removeWhere = function (func) {
            for (var i = 0; i < boardSelf.tiles.length; i++) {
                if (func(boardSelf.tiles[i])) {
                    var x = boardSelf.getX(i);
                    var y = boardSelf.getY(i);

                    var newTile = {};
                    boardSelf.newTile(y, x, newTile);
                    boardSelf.setTile(y, x, newTile);
                    newTile.reRender();
                }
            }
        };

        boardSelf.isFull = function () {
            var tiles = boardSelf.tiles;
            for (var i = 0; i < tiles.length; i++) {
                if (typeof tiles[i]['render'] === 'undefined') {
                    return false;
                }
            }
            return true;
        };


        boardSelf.getRenderedTile = function (y, x) {
            return $('[data-yx="' + boardSelf.name + '-' + y + '-' + x + '"]');
        };

        boardSelf.getRenderedCell = function (y, x) {
            return boardSelf.getRenderedTile(y, x).parent('td');
        };

        boardSelf.click = function (elm) {
            var yx = $(elm).attr('data-yx').split('-');
            var y = +yx[1];
            var x = +yx[2];
            var tile = boardSelf.getTile(y, x);
            if (typeof tile['click'] === 'function') {
                tile.click();
            }
        };

        boardSelf.render = function (target) {
            if (typeof target === 'undefined') {
                if (typeof boardSelf.$target === 'undefined') {
                    target = '.gameon-board';
                }
                else {
                    target = boardSelf.$target;
                }
            }
            boardSelf.$target = $(target);
            var $domtable = $('<table></table>');
            var popups = boardSelf.$target.find('.gameon-board-popups');
            if (!popups.length) {
                boardSelf.$target.append('<div class="gameon-board-popups"></div>');
            }
            for (var h = 0; h < boardSelf.height; h++) {
                var $currentRow = $('<tr></tr>');
                for (var w = 0; w < boardSelf.width; w++) {
                    var even = 'odd';
                    if ((h + w) % 2 === 0) {
                        even = 'even';
                    }
                    var $currentCell = $('<td class="' + even + '"></td>');

                    var tile = boardSelf.getTile(h, w);
                    if (typeof tile !== 'undefined' && typeof tile['tileRender'] === 'function') {
                        $currentCell.append(tile.tileRender());
                    }

                    $currentRow.append($currentCell);
                }
                $domtable.append($currentRow);
            }
            boardSelf.$target.find('table').remove();
            boardSelf.$target.append($domtable);
        };

        boardSelf.getContainerAt = function (y, x) {
            return boardSelf.$target.find('tr:nth-child(' + (y + 1) + ') td:nth-child(' + (x + 1) + ')');
        };

        boardSelf.getPathFromTo = function (startTile, endTile, diagonalAllowed) {
            if (!startTile || !endTile) {
                return null;
            }
            if (typeof diagonalAllowed == 'undefined') {
                diagonalAllowed = false;
            }

            var start = [startTile.yPos, startTile.xPos];
            var goal = [endTile.yPos, endTile.xPos];
            var seen = [];
            var previous = [];
            for (var y = 0; y < boardSelf.height; y++) {
                seen.push([]);
                previous.push([]);
                for (var j = 0; j < boardSelf.width; j++) {
                    seen[y].push(false);
                    previous[y].push([])
                }
            }
            seen[start[0]][start[1]] = true;

            var queue = new Queue(),
                next = start;

            function visit() {
                if (boardSelf.isInBoard(currYPos, currXPos) && !seen[currYPos][currXPos] && boardSelf.getTile(currYPos, currXPos).canPassThrough) {
                    seen[currYPos][currXPos] = true;
                    previous[currYPos][currXPos] = [ypos, xpos];
                    queue.enqueue([currYPos, currXPos])
                }
            }

            while (next) {
                var xpos = next[1];
                var ypos = next[0];

                //left right up down
                var currXPos = xpos - 1;
                var currYPos = ypos;
                visit();
                currXPos = xpos + 1;
                visit();
                currXPos = xpos;
                currYPos = ypos - 1;
                visit();
                currYPos = ypos + 1;
                visit();

                if (diagonalAllowed) {
                    currXPos = xpos + 1;
                    currYPos = ypos + 1;
                    visit();
                    currXPos = xpos + 1;
                    currYPos = ypos - 1;
                    visit();
                    currXPos = xpos - 1;
                    currYPos = ypos + 1;
                    visit();
                    currXPos = xpos - 1;
                    currYPos = ypos - 1;
                    visit();
                }

                next = queue.dequeue();
                if (!next) {
                    return null;
                }
                if (next[0] == goal[0] && next[1] == goal[1]) {
                    var backtrace = [next];
                    var current = next;
                    while (!(current[0] == start[0] && current[1] == start[1])) {
                        current = previous[current[0]][current[1]];
                        backtrace.push(current)
                    }
                    return backtrace.reverse();
                }
            }
        };

        boardSelf.getAllReachableTilesFrom = function (startTile) {
            if (!startTile) {
                return [];
            }

            var seen = [];
            for (var y = 0; y < boardSelf.height; y++) {
                seen.push([]);
                for (var j = 0; j < boardSelf.width; j++) {
                    seen[y].push(false);
                }
            }
            seen[startTile.yPos][startTile.xPos] = true;
            var availableMoves = [];

            var stack = [],
                next = startTile;
            while (next) {
                var ypos = next.yPos;
                var xpos = next.xPos;

                //left right up down
                var currXPos = xpos - 1;
                var currYPos = ypos;
                if (boardSelf.isInBoard(currYPos, currXPos) && !seen[currYPos][currXPos] && boardSelf.getTile(currYPos, currXPos).canPassThrough) {
                    seen[currYPos][currXPos] = true;
                    var possibleMove = boardSelf.getTile(currYPos, currXPos);
                    stack.push(possibleMove);
                    availableMoves.push(possibleMove);
                }
                currXPos = xpos + 1;
                if (boardSelf.isInBoard(currYPos, currXPos) && !seen[currYPos][currXPos] && boardSelf.getTile(currYPos, currXPos).canPassThrough) {
                    seen[currYPos][currXPos] = true;
                    var possibleMove = boardSelf.getTile(currYPos, currXPos);
                    stack.push(possibleMove);
                    availableMoves.push(possibleMove);
                }
                currXPos = xpos;
                currYPos = ypos - 1;
                if (boardSelf.isInBoard(currYPos, currXPos) && !seen[currYPos][currXPos] && boardSelf.getTile(currYPos, currXPos).canPassThrough) {
                    seen[currYPos][currXPos] = true;
                    var possibleMove = boardSelf.getTile(currYPos, currXPos);
                    stack.push(possibleMove);
                    availableMoves.push(possibleMove);
                }
                currYPos = ypos + 1;
                if (boardSelf.isInBoard(currYPos, currXPos) && !seen[currYPos][currXPos] && boardSelf.getTile(currYPos, currXPos).canPassThrough) {
                    seen[currYPos][currXPos] = true;
                    var possibleMove = boardSelf.getTile(currYPos, currXPos);
                    stack.push(possibleMove);
                    availableMoves.push(possibleMove);
                }

                next = stack.pop();
                if (!next) {
                    return availableMoves;
                }
            }
        };

        boardSelf.animateTileAlongPath = function (tile, path, animationTime, callback) {
            if (self.noAnimation) {
                animationTime = 0;
            }

            var timescalled = 0;
            var cellWidth = boardSelf.$target.find('td').outerWidth();

            function handleAnimation() {
                //custom animation followed by update

                var currentPos = timescalled;
                var nextPos = timescalled + 1;

                var newcss = {};
                if (path[currentPos][1] > path[nextPos][1]) {
                    newcss['left'] = '-=' + cellWidth
                }
                if (path[currentPos][1] < path[nextPos][1]) {
                    newcss['left'] = '+=' + cellWidth
                }
                if (path[currentPos][0] > path[nextPos][0]) {
                    newcss['top'] = '-=' + cellWidth
                }
                if (path[currentPos][0] < path[nextPos][0]) {
                    newcss['top'] = '+=' + cellWidth
                }
                timescalled++;
                var stopping = timescalled >= path.length - 1;

                var $renderedTile = boardSelf.getRenderedTile(tile.yPos, tile.xPos);
                if (!stopping) {
                    $renderedTile.animate(newcss, animationTime, handleAnimation);
                }

                if (stopping) {
                    //last time
                    $renderedTile.animate(newcss, animationTime, function () {
                        //stop animation
                        $renderedTile.css({
                            left: '0px',
                            top: '0px'
                        });

                        callback();
                    })

                }
            }

            handleAnimation();
        };

        var fadingPopupCounter = 0;

        boardSelf.fadingPopup = function (content) {
            fadingPopupCounter++;

            var $container = boardSelf.$target.find('.gameon-board-popups');
            var $popup = $('<div class="gameon-board-popups__popup">' + content + '</div>');
            //get top and left values
            var $boardTable = boardSelf.$target.find('table');
            var boardHeight = $boardTable.outerHeight();
            var boardWidth = $boardTable.outerWidth();

            var positionSequence = [7, 3, 5, 9, 2, 4, 8, 1, 6];
            var positions = [];
            for (var y = 1; y <= 3; y++) {
                for (var x = 0; x < 3; x++) {
                    positions.push([y / 3 * (boardHeight) + 100 - boardHeight / 2, x / 3 * (boardWidth) + 4 - boardWidth / 2])
                }
            }
            fadingPopupCounter %= positionSequence.length;

            var position = positions[positionSequence[fadingPopupCounter] - 1];
            $popup.css({top: position[0], left: position[1]});

            $container.append($popup);
            $popup.animate({top: '-=100px', opacity: 0}, 4000, function () {
                $popup.remove();
            });
        };

        boardSelf.falldown = function (newTiles, callback) {

            //work out the required state column by column and set the internal data to that straight away.
            //animate towards that state
            //refreshui
            var tiledist = boardSelf.$target.find('td').outerHeight();
            var falltime = 0.20;
            if (self.noAnimation) {
                falltime = 0;
            }
            var maxNumDeletedPerColumn = 0;
            var newTileNum = 0;
            for (var w = 0; w < boardSelf.width; w++) {

                var numDeleted = 0;
                for (var h = boardSelf.height - 1; h >= 0; h--) {
                    var currTile = boardSelf.getTile(h, w);

                    var renderedTile = boardSelf.getRenderedTile(currTile.yPos, currTile.xPos);
                    if (currTile.deleted) {
                        numDeleted += 1;
                        if (numDeleted > maxNumDeletedPerColumn) {
                            maxNumDeletedPerColumn = numDeleted;
                        }
                        renderedTile.remove();
                    } else {
                        if (numDeleted == 0) {
                            continue;
                        }
                        var endPos = h + numDeleted;
                        var fallDistance = numDeleted * tiledist;
                        var container = boardSelf.getContainerAt(endPos, w);

                        var renderedTile = boardSelf.getRenderedTile(h, w);
                        renderedTile.attr('data-yx', boardSelf.name + '-' + endPos + '-' + w);
                        container.html(renderedTile);

                        renderedTile = boardSelf.getRenderedTile(endPos, w);
                        renderedTile.css({top: -fallDistance});
                        renderedTile.animate({top: '+=' + fallDistance}, tiledist / (falltime / numDeleted));


                        //update our model
                        currTile.yPos = endPos;
                        currTile.xPos = w;
                        boardSelf.setTile(endPos, w, currTile);
                    }
                }
                for (var h = 0; h < numDeleted; h++) {
                    var currNewTile = newTiles[newTileNum++];
                    boardSelf.newTile(h, w, currNewTile);

                    //update our model
                    boardSelf.setTile(h, w, currNewTile);

                    var container = boardSelf.getContainerAt(h, w);

                    var fallDistance = numDeleted * tiledist;

                    container.html(currNewTile.tileRender({top: -fallDistance}));
                    var renderedTile = boardSelf.getRenderedTile(h, w);
                    renderedTile.animate({top: '+=' + fallDistance}, tiledist / (falltime / numDeleted));
                }

            }

            setTimeout(callback, maxNumDeletedPerColumn * falltime)
        };

        boardSelf.view = function () {
            //todo custom tileview with a proper contains method?
            return new self.ArrayView(boardSelf.tiles);
        };
        boardSelf.viewWhere = function (where) {
            var tiles = [];
            for (var i = 0; i < boardSelf.tiles.length; i++) {
                var tile = boardSelf.tiles[i];
                if (where(tile)) {
                    tiles.push(tile);
                }
            }
            return new self.ArrayView(tiles);
        };
        boardSelf.viewOfWhere = function (of, where) {
            var tiles = [];
            for (var i = 0; i < boardSelf.tiles.length; i++) {
                var tile = boardSelf.tiles[i];
                if (where(tile)) {
                    tiles.push(of(tile));
                }
            }
            return new self.ArrayView(tiles);
        };
        construct(width, height, tiles);
        return boardSelf;
    };

    self.ArrayView = function (arr) {
        var viewSelf = {};
        if (typeof arr === 'undefined') {
            arr = []
        }
        function construc() {
            viewSelf.arr = arr;
            viewSelf.largePrimes = [1298809, 1298951, 1299059, 1299203, 1299299, 1299379, 1299541, 1299689, 1299827];
            viewSelf.shuffle();
        }

        viewSelf.get = function (i) {
            return arr[i];
        };
        viewSelf.shuffledGet = function (i) {
            var idx = viewSelf.hash(i);
            return viewSelf.get(idx);
        };
        viewSelf.shuffledGet2 = function (i) {
            var idx = viewSelf.hash2(i);
            return viewSelf.get(idx);
        };
        viewSelf.hash = function (i) {
            return (viewSelf.hashstart + (i * viewSelf.hashstep))
                % viewSelf.length();
        };
        viewSelf.hash2 = function (i) {
            return (viewSelf.hashstart2 + (i * viewSelf.hashstep2))
                % viewSelf.length();
        };
        viewSelf.length = function () {
            return arr.length;
        };
        viewSelf.shuffle = function () {
            viewSelf.primeIdx = self.math.numberBetween(0, viewSelf.largePrimes.length);
            viewSelf.hashstep = viewSelf.largePrimes[viewSelf.primeIdx] % viewSelf.length();
            viewSelf.hashstart = self.math.numberBetween(0, viewSelf.length());

            viewSelf.primeIdx2 = self.math.numberBetween(0, viewSelf.largePrimes.length);
            viewSelf.hashstep2 = viewSelf.largePrimes[viewSelf.primeIdx2] % viewSelf.length();
            viewSelf.hashstart2 = self.math.numberBetween(0, viewSelf.length());
        };
        viewSelf.contains = function (x) {
            return arr.indexOf(x) === -1;
        };
        construc();
        return viewSelf;
    };


    self.math = new (function () {
        var mathSelf = this;
        mathSelf.numberBetween = function (a, b) {
            return Math.floor(Math.random() * (b - a) + a);
        };

        mathSelf.NumberLine = function (low, high, step) {
            var lineSelf = new self.ArrayView();
//            $.extend(true, lineSelf, new self.ArrayView());
            //TODO support capping the number of digits?

            function construc() {
                lineSelf.low = low;
                lineSelf.high = high;
                lineSelf.step = step;
                lineSelf.shuffle();
            }

            lineSelf.get = function (i) {
                return lineSelf.low + (lineSelf.step * i);
            };
            lineSelf.length = function () {
                return +((lineSelf.high - lineSelf.low) / step);
            };
            lineSelf.contains = function (x) {
                function fromFP(y) {
                    return Math.round(y * 100000);
                }

                return x >= lineSelf.low && x < lineSelf.high &&
                    fromFP(x) % fromFP(lineSelf.step) == 0;
            };
            construc();
            return lineSelf;
        };

        mathSelf.round = function (num, numDecimalPlaces) {
            var tx = Math.pow(10, numDecimalPlaces);
            return Math.round((num + 0.00001) * tx) / tx;
        };

        /**
         * a bit hack
         * @param x
         * @param precision eg .1 .01 or .001 depending on the number of decimal places you want
         */
        mathSelf.precisionRound = function (x, precision) {
            var str = '' + precision;
            var numDecimalPlaces = 0;
            if (str.length >= 3) {
                numDecimalPlaces = str.length - 2;
            }
            return mathSelf.round(x, numDecimalPlaces)
        }

    })();


    self.StarBar = function (starrating, extraClass) {
        var starSelf = this;
        starSelf.$starBar = $($.trim($('.gameon-starbar-template').html()));

        if (starrating.length == 1) {
            starSelf.end = starrating[0];
            starSelf.$starBar.find('.gameon-starbar__stars').hide();
        }
        else {
            starSelf.one = starrating[0];
            starSelf.two = starrating[1];
            starSelf.three = starrating[2];
            starSelf.end = starrating[3];
        }
        if (typeof extraClass == 'undefined') {
            extraClass = 'progress-bar-success'
        }
        starSelf.$starBar.find('.gameon-starbar__track').addClass(extraClass);

        starSelf.movesScores = [];
        starSelf.movesBonus = null;
        starSelf.timeBonus = null;

        starSelf.numStars = 0;
        starSelf._score = 0;


        starSelf.setScore = function (score) {
            starSelf._score = score;
            starSelf.update();
        };
        starSelf.addMoveScoring = function (score) {
            starSelf.movesScores.push(score);
            starSelf._score += score;
            starSelf.update();
        };
        starSelf.addMovesBonus = function (moves) {
            var averageScorePerMove = Math.ceil(starSelf.movesScores.average());
            var bonus = moves * averageScorePerMove * 2;
            starSelf.movesBonus = {
                moves: moves,
                averageScorePerMove: averageScorePerMove,
                bonus: bonus
            };
            starSelf._score += bonus;
        };
        starSelf.getScore = function () {
            return starSelf._score;
        };
        starSelf.setCenterMessage = function (message) {
            starSelf.$target.find('.gameon-starbar__center-message').html(message);
        };
        starSelf.addTimeBonus = function (totalTime, timeLeft) {
            var averageScorePerMove = Math.ceil(starSelf.movesScores.average());
            var averageNumMovesPerSecond = starSelf.movesScores.length / totalTime;
            var bonus = Math.ceil(averageNumMovesPerSecond * averageScorePerMove * timeLeft * 2);
            starSelf.timeBonus = {
                timeLeft: timeLeft,
                averageScorePerMove: averageScorePerMove,
                averageNumMovesPerSecond: averageNumMovesPerSecond,
                bonus: bonus
            };
            starSelf._score += bonus;
        };
        starSelf.hasWon = function () {
            return starSelf._score >= starSelf.one;
        };
        starSelf.hasFullScore = function () {
            return starSelf._score >= starSelf.end;
        };

        starSelf.update = function () {
            var conpleteRatio = starSelf._score / starSelf.end;
            starSelf.$starBar.find(".gameon-starbar__track").css("width", conpleteRatio * 100 + '%');

            var numStars = 0;

            if (starSelf._score >= starSelf.one) {
                starSelf.$starBar.find('.gameon-starbar__star--one').addClass('gameon-star--shiny');
                numStars++;
            }
            else {
                starSelf.$starBar.find('.gameon-starbar__star--one').removeClass('gameon-star--shiny');
            }

            if (starSelf._score >= starSelf.two) {
                starSelf.$starBar.find('.gameon-starbar__star--two').addClass('gameon-star--shiny');
                numStars++;
            }
            else {
                starSelf.$starBar.find('.gameon-starbar__star--two').removeClass('gameon-star--shiny');
            }

            if (starSelf._score >= starSelf.three) {
                starSelf.$starBar.find('.gameon-starbar__star--three').addClass('gameon-star--shiny');
                numStars++;
            }
            else {
                starSelf.$starBar.find('.gameon-starbar__star--three').removeClass('gameon-star--shiny');
            }

            if (numStars > starSelf.numStars) {
                self.playSound('doublepoints');
            }
            starSelf.numStars = numStars;

            starSelf.$starBar.find('.gameon-starbar__score').html(starSelf._score);
        };

        starSelf.render = function (target) {
            starSelf.$target = $(target);

            var starOnePos = (starSelf.one / starSelf.end) * 100;
            var starTwoPos = (starSelf.two / starSelf.end) * 100;
            var starThreePos = (starSelf.three / starSelf.end) * 100;
            starSelf.$starBar.find('.gameon-starbar__star--one').css({left: starOnePos + '%'});
            starSelf.$starBar.find('.gameon-starbar__star--two').css({left: starTwoPos + '%'});
            starSelf.$starBar.find('.gameon-starbar__star--three').css({left: starThreePos + '%'});
            starSelf.$target.html(starSelf.$starBar);
            starSelf.update();
        }
    };

    self.Stars = function (ratingScheme, score) {
        var starSelf = this;
        starSelf.ratingScheme = ratingScheme;
        starSelf.score = score;

        starSelf.render = function () {
            var output = ['<div class="gameon-stars">'];
            for (var i = 0; i < 3; i++) {
                var thresh = starSelf.ratingScheme[i];
                if (starSelf.score >= thresh) {
                    output.push('<span class="fa gameon-star gameon-star--shiny gameon-star--' + i + '"></span>');
                }
                else {
                    output.push('<span class="fa gameon-star gameon-star--' + i + '"></span>');
                }
            }
            output.push('</div>');
            return output.join('');
        }
    };

    self.unlock = function (target) {
        var $button = $(target).find('button');
        if ($button.length > 0) {
            $button.removeAttr('disabled');
            $button.find('.glyphicon-lock').remove();
        }
        else {
            var $button = $(target);
            $button.removeClass('disabled');
            $button.find('.glyphicon-lock').remove();
        }
    };
    self.isLocked = function (target) {
        var $button = $(target).find('button');
        return $button.attr('disabled');
    };

    self.shuffle = function (arr) {
        for (var i = arr.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
        }

        return arr;
    };

    self.gotoLink = function (link) {
        if (!self.isInIFrame()) {
            window.location = $(link).attr('href');
            return false;
        }
        return true
    };

    self.isInIFrame = function () {
        return window != window.top
    };

    return self;
})();
