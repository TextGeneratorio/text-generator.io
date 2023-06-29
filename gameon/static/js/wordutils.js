window.gameon = window.gameon || {};
window.gameon.wordutils = new (function () {
    "use strict";
    var self = this;

    var word_frequencies = {
        'E': 12.02,
        'T': 9.10,
        'A': 8.12,
        'O': 7.68,
        'I': 7.31,
        'N': 6.95,
        'S': 6.28,
        'R': 6.02,
        'H': 5.92,
        'D': 4.32,
        'L': 3.98,
        'U': 2.88,
        'C': 2.71,
        'M': 2.61,
        'F': 2.30,
        'Y': 2.11,
        'W': 2.09,
        'G': 2.03,
        'P': 1.82,
        'B': 1.49,
        'V': 1.11,
        'K': 0.69,
        'X': 0.17,
        'Q': 0.11,
        'J': 0.10,
        'Z': 0.07
    };

    var scrabbleScoring = {
        'A': 1,
        'B': 3,
        'C': 3,
        'D': 2,
        'E': 1,
        'F': 4,
        'G': 2,
        'H': 4,
        'I': 1,
        'J': 8,
        'K': 5,
        'L': 1,
        'M': 3,
        'N': 1,
        'O': 1,
        'P': 3,
        'Q': 10,
        'R': 1,
        'S': 1,
        'T': 1,
        'U': 1,
        'V': 4,
        'W': 4,
        'X': 8,
        'Y': 4,
        'Z': 10
    };

    function cdf(hist) {
        var keys = Object.keys(hist);
        for (var i = 1; i < keys.length; i++) {
            hist[keys[i]] = hist[keys[i]] + hist[keys[i - 1]];
        }
        return hist;
    }

    var word_cdf = cdf(word_frequencies);

    self.getRandomLetter = function () {
        var position = Math.random();
        var keys = Object.keys(word_cdf);
        for (var i = 0; i < keys.length; i++) {
            if (position <= word_cdf[keys[i]] / 100) {
                return keys[i];
            }
        }
    };

    self.scoreWord = function (word) {
        var score = 0;
        for (var i = 0; i < word.length; i++) {
            score += scrabbleScoring[word[i].toUpperCase()];
        }
        return score;
    };
    self.scoreLetter = function (l) {
        return scrabbleScoring[l.toUpperCase()];
    };

    self.capitaliseFirstLetter = function (word) {
        return word.charAt(0).toUpperCase() + word.slice(1);
    }
});
