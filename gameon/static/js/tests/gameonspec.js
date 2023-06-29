describe("setup", function () {
    it("should delete scores", function (done) {
        gameon.getUser(function (user) {

            user.deleteAllScores(function () {
                expect(user.scores).toEqual([]);
                delete gameon.user;
                window.setTimeout(function () {
                    gameon.getUser(function (user2) {
                        expect(user2.scores).toEqual([]);
                        done();
                    });
                }, 1000);
            });
        });
    });
});

describe("gameon", function () {

    it("should be able to play music (looping)", function (done) {
        gameon.loadSound("music", '/gameon/static/music/ws-theme.mp3');
        gameon.loopSound("music");
        done()
    });

    it("should be able to play sounds", function (done) {
        gameon.loadSound("sound", '/gameon/static/music/doublepoints.m4a');
        gameon.playSound("sound");
        done()
    });

    it("should be able to get a user", function (done) {
        gameon.getUser(function (user) {
            expect(user.volume).toBeDefined();
            done();
        })
    });

    describe("when scores have been added", function () {
        var once = 0;
        beforeEach(function (done) {
            if (once === 1) {
                done();
                return;
            }
            once = 1;
            gameon.getUser(function (user) {
                var times = 0;

                function saveCallback(data) {
                    times++;
                    if (times >= 3) {
                        done();
                    }
                }

                user.saveScore(-1, 123, saveCallback);
                user.saveScore(-3, 123, saveCallback);
                user.saveScore(-2, 123, saveCallback);
            });
        });

        it("should be able to get a user with scores", function (done) {
            gameon.getUser(function (user) {
                expect(user.scores[0].score).toEqual(123);
                expect(user.scores[0].game_mode).toEqual(-3);
                expect(user.scores[1].score).toEqual(123);
                expect(user.scores[1].game_mode).toEqual(-2);
                expect(user.scores[2].score).toEqual(123);
                expect(user.scores[2].game_mode).toEqual(-1);
                done();
            });
        });
        it("should be able to get a fresh user with scores", function (done) {
            delete gameon.user;
            window.setTimeout(function () {
                gameon.getUser(function (user) {
                    // saving scores is not ran in a transaction so we don't know what we will get :/
                    expect(user.scores.length).toBeGreaterThan(0);
                    done();
                });
            }, 1000);
        });
        it("should be able to get highscores", function (done) {
            gameon.getUser(function (user) {
                user.scores = [
                    {'game_mode': 1, 'score': 1},
                    {'game_mode': 1, 'score': 2},
                    {'game_mode': 1, 'score': 1},
                    {'game_mode': 2, 'score': 2},
                    {'game_mode': 2, 'score': 1},
                    {'game_mode': 3, 'score': 3}
                ];
                var scores = user.getHighScores();
                expect(scores.length).toEqual(3);
                expect(scores[0].score).toEqual(2);
                expect(scores[1].score).toEqual(2);
                expect(scores[2].score).toEqual(3);
                done();
            });
        });
    });

    describe("when achievements have been added", function () {
        var achievementType = 1;
        beforeEach(function (done) {
            gameon.getUser(function (user) {
                user.saveAchievement(achievementType, function (data) {
                    done();
                })
            })
        });

        it("should be able to get a user with an achievement", function (done) {
            gameon.getUser(function (user) {
                expect(user.achievements[0].type).toEqual(achievementType);
                done();
            })
        });
        it("should be able to get a fresh user with an achievement", function (done) {
            delete gameon.user;
            window.setTimeout(function () {
                gameon.getUser(function (user) {
                    expect(user.achievements[0].type).toEqual(achievementType);
                    done();
                })
            }, 1000);
        });
    });

    describe("when a user has had data edited", function () {
        var achievementType = 1;
        var volume = 0.2;
        var mute = 1;
        var levels_unlocked = 10;
        var difficulties_unlocked = 3;
        specHelpers.beforeAll(function (done) {
            gameon.getUser(function (user) {
                var numCallsRequired = 4;
                var numCallsCompleted = 0;

                function doneFunc(data) {
                    numCallsCompleted++;
                    if (numCallsCompleted >= numCallsRequired) {
                        done()
                    }
                }

                user.saveVolume(volume, doneFunc);
                user.saveMute(mute, doneFunc);
                user.saveLevelsUnlocked(levels_unlocked, doneFunc);
                user.saveDifficultiesUnlocked(difficulties_unlocked, doneFunc)
            })
        });

        it("should have correct volume", function (done) {
            gameon.getUser(function (user) {
                expect(user.volume).toEqual(volume);
                done();
            })
        });
        it("should have correct mute", function (done) {
            gameon.getUser(function (user) {
                expect(user.mute).toEqual(mute);
                done();
            })
        });
        it("should have correct levels_unlocked", function (done) {
            gameon.getUser(function (user) {
                expect(user.levels_unlocked).toEqual(levels_unlocked);
                done();
            })
        });
        it("should have correct difficulties_unlocked", function (done) {
            gameon.getUser(function (user) {
                expect(user.difficulties_unlocked).toEqual(difficulties_unlocked);
                done();
            })
        });

        it("should have persisted user data", function (done) {
            delete gameon.user;

            window.setTimeout(function () {
                gameon.getUser(function (user) {
                    expect(user.volume).toEqual(volume);
                    expect(user.mute).toEqual(mute);
                    expect(user.levels_unlocked).toEqual(levels_unlocked);
                    expect(user.difficulties_unlocked).toEqual(difficulties_unlocked);
                    done();
                });
            }, 1000);
        });
    });
    //the clock is now untestable because we cant tell it when to call setInterval :(
//    describe("the clock is started", function () {
//        var seconds = 2;
//        var clock = {};
//        beforeEach(function () {
//            function gameOver() {
//
//            }
//
//            jasmine.clock().install();
//            clock = new gameon.clock(gameOver, seconds);
//        });
//
//        afterEach(function () {
//            jasmine.clock().uninstall();
//        });
//
//        it("should be able to start pause unpause", function (done) {
//            clock.start();
//            clock.pause();
//            clock.unpause();
//            done();
//        });
//        it("it should go down + gameover should be called ONCE when the clock runs out", function (done) {
//            var times = 0;
//            function gameOver() {
//                times ++;
//            }
//
//            var clock2 = new gameon.clock(gameOver, seconds);
//
//            clock2.start();
//            jasmine.clock().tick(1001);
//            expect(clock2.seconds).toEqual(seconds - 1);
//            jasmine.clock().tick(1001);
//            jasmine.clock().tick(99999);
//            expect(times).toEqual(1);
//            done();
//
//        });
//    });

    // ========== BOARD STUFF =================
    var board;
    var Tile = function () {
        var self = this;
        self.number = gameon.math.numberBetween(1, 5);
        self.click = function () {
        };
        self.render = function () {
            return '<button type="button" class="btn btn-danger btn-lg">' + self.number + '</button>';
        };
    };
    it("should be able to create & render a board", function (done) {
        var tiles = [];
        for (var i = 0; i < 5; i++) {
            for (var j = 0; j < 5; j++) {
                var tile = new Tile();
                tile.click = function () {
                    console.log('click');
                    done();
                };
                tiles.push(tile);

            }
        }
        board = new gameon.Board(5, 5, tiles);
        board.render();
        $('[data-yx="' + board.name + '-0-0"]').trigger('mousedown');
    });

    it("board should be able to get paths", function (done) {
        var path = board.getPathFromTo({xPos: 0, yPos: 0}, {xPos: 4, yPos: 4});
        expect(path).toEqual(null);

        var tiles = [];
        for (var i = 0; i < 5; i++) {
            for (var j = 0; j < 5; j++) {
                var tile = new Tile();
                tile.canPassThrough = true;
                tile.click = function () {
                    console.log('click');
                    done();
                };
                tiles.push(tile);

            }
        }
        var movableBoard = new gameon.Board(5, 5, tiles);

        var path = movableBoard.getPathFromTo({xPos: 0, yPos: 0}, {xPos: 4, yPos: 4});
        expect(path.length).toBe(9);
        expect(path[0]).toEqual([0, 0]);
        expect(path[8]).toEqual([4, 4]);

        var reachableTiles = movableBoard.getAllReachableTilesFrom(movableBoard.getTile(0,0));
        expect(reachableTiles.length).toBe(24);

        var tiles = [];
        for (var i = 0; i < 5; i++) {
            for (var j = 0; j < 5; j++) {
                var tile = new Tile();
                tile.canPassThrough = true;
                if (i == 2) {
                    tile.canPassThrough = false;
                }
                tile.click = function () {
                    console.log('click');
                    done();
                };
                tiles.push(tile);

            }
        }
        var movableBoard = new gameon.Board(5, 5, tiles);

        var path = movableBoard.getPathFromTo({xPos: 0, yPos: 0}, {xPos: 4, yPos: 4});
        expect(path).toEqual(null);
        var path = movableBoard.getPathFromTo({xPos: 4, yPos: 0}, {xPos: 4, yPos: 4});
        expect(path).toEqual(null);
        var path = movableBoard.getPathFromTo({xPos: 0, yPos: 4}, {xPos: 4, yPos: 4});
        expect(path.length).toBe(5);

        var path = movableBoard.getPathFromTo(null, {xPos: 4, yPos: 4});
        expect(path).toEqual(null);


        var reachableTiles = movableBoard.getAllReachableTilesFrom(movableBoard.getTile(0, 0));
        expect(reachableTiles.length).toBe(9);

        var reachableTiles = movableBoard.getAllReachableTilesFrom(movableBoard.getTile(2, 0));
        expect(reachableTiles.length).toBe(20);

        done();
    });
    it("board should be able to swap tiles", function (done) {
        var tile00 = board.getTile(1, 0);
        var tile44 = board.getTile(3, 4);
        board.swapTiles({xPos: 0, yPos: 1}, {xPos: 4, yPos: 3});
        var expectedTile44 = board.getTile(1, 0);
        var expectedTile00 = board.getTile(3, 4);
        expect(tile00).toEqual(expectedTile00);
        expect(tile44).toEqual(expectedTile44);

        var tile00 = board.getTile(1, 0);
        var tile44 = board.getTile(3, 4);
        board.swapTiles(1, 0, 3, 4);
        var expectedTile44 = board.getTile(1, 0);
        var expectedTile00 = board.getTile(3, 4);
        expect(tile00).toEqual(expectedTile00);
        expect(tile44).toEqual(expectedTile44);

        var tile00 = board.getTile(1, 0);
        var tile44 = board.getTile(3, 4);
        board.swapTiles([1, 0], [3, 4]);
        var expectedTile44 = board.getTile(1, 0);
        var expectedTile00 = board.getTile(3, 4);
        expect(tile00).toEqual(expectedTile00);
        expect(tile44).toEqual(expectedTile44);

        done();

    });
    it("board should be able to show fading popups", function (done) {
        for (var i = 0; i < 10; i++) {
            board.fadingPopup('<button type="button" class="btn btn-success">0 Points!</button>')
        }

        done();

    });
    it("board should be able to delete tiles and do a falldown animation", function (done) {
        var endPos = board.tiles.length - 1;

        board.tiles[endPos].deleted = true;
        board.tiles[endPos - 1].deleted = true;
        board.tiles[endPos - 2].deleted = true;
        board.tiles[endPos - 3].deleted = true;
        board.tiles[endPos - 4].deleted = true;
        board.tiles[5].deleted = true;

        var newTiles = [];
        for (var j = 0; j < 6; j++) {
            var tile = new Tile();
            tile.click = function () {
                console.log('click');
                done();
            };
            newTiles.push(tile);
        }
        board.falldown(newTiles, function () {
            board.render();
            board.tiles[endPos - 1].deleted = true;

            var newTiles = [];
            for (var j = 0; j < 1; j++) {
                var tile = new Tile();
                tile.click = function () {
                    console.log('click');
                    done();
                };
                newTiles.push(tile);
            }
            board.falldown(newTiles, function () {
            })
        });
        done();
    });

    it("should be able to create a star bar", function (done) {
        var starBar = new gameon.StarBar([20, 40, 60, 100]);
        starBar.setScore(10);
        expect(starBar.numStars).toBe(0);
        starBar.render('.gameon-test-starbar');
        starBar.setScore(21);
        expect(starBar.numStars).toBe(1);
        starBar.setScore(40);
        expect(starBar.numStars).toBe(2);
        starBar.setScore(60);
        starBar.setScore(70);
        expect(starBar.numStars).toBe(3);

        var blueStarBar = new gameon.StarBar([20, 40, 60, 100], 'progress-bar-primary');
        blueStarBar.setScore(60);
        blueStarBar.render('.gameon-test-blue-starbar');

        var redStarBar = new gameon.StarBar([20, 40, 60, 100], 'progress-bar-danger');
        redStarBar.setScore(70);
        redStarBar.render('.gameon-test-red-starbar');

        var noStarBar = new gameon.StarBar([100], 'progress-bar-info');
        noStarBar.setScore(80);
        noStarBar.render('.gameon-test-no-star-starbar');

        expect(blueStarBar.getScore()).toBe(60);
        expect(redStarBar.getScore()).toBe(70);
        expect(noStarBar.getScore()).toBe(80);
        done();

    });
    it("should have a correct math package", function (done) {
        var maths = gameon.math;
        expect(maths.numberBetween(1, 2)).toBe(1);
        expect(maths.numberBetween(0, 1)).toBe(0);


        var low = 0;
        var step = 0.1;
        var numline = new maths.NumberLine(low, 10, step);
        expect(numline.length()).toBe(100);
        var expectedTotal = 0;
        var currNum = low;
        for (var i = 0; i < numline.length(); i++) {
            expectedTotal += currNum;
            currNum += step;
        }
        expectedTotal = Math.round(expectedTotal);
        var total = 0;
        for (var i = 0; i < numline.length(); i++) {
            total += numline.shuffledGet(i);
        }
        expect(Math.round(total)).toBe(expectedTotal);


        var got = gameon.math.precisionRound(1.11, 0.1);
        expect(got).toBe(1.1);
        var got = gameon.math.precisionRound(1.1111, 0.01);
        expect(got).toBe(1.11);
        var got = gameon.math.precisionRound(1.11, 0.0001);
        expect(got).toBe(1.11);
        var got = gameon.math.precisionRound(1, 0.1);
        expect(got).toBe(1);
        var got = gameon.math.precisionRound(1.11, 1);
        expect(got).toBe(1);
        done();
    });

});
