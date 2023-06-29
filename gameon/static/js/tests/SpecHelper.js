//beforeEach(function() {
//  this.addMatchers({
//    toBePlaying: function(expectedSong) {
//      var player = this.actual;
//      return player.currentlyPlayingSong === expectedSong &&
//             player.isPlaying;
//    }
//  });
//});
var specHelpers = new (function () {
    'use strict';
    var self = this;

    self.clickBtn = function (target) {
        $(target + ' button').click();
    };

    self.deleteCookie = function (name) {
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    };


    self.beforeAll = function (func) {
        var calledTimes = 0;

        var calledOnceFunc = function (done) {
            if (calledTimes >= 1) {
                done();
            }
            else {
                func(done)
            }
        };
        beforeEach(calledOnceFunc);
    };

    self.onceFunction = $.noop;
    self.once = function(fun) {
        if (typeof fun == 'undefined') {
            self.onceFunction();
            self.onceFunction = $.noop;
        }
        else {
            self.onceFunction = fun;
        }
    }

})();
