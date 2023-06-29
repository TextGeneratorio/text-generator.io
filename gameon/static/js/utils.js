(function ($) {
    $.event.special.destroyed = {
        remove: function (o) {
            if (o.handler) {
                o.handler();
            }
        }
    };
})(jQuery);

window.gameon = window.gameon || {};
window.gameon.blockUI = function (message) {
    if (typeof message == "undefined") {
        message = '';
    }
    $.blockUI({ message: message});
};
window.gameon.unblockUI = function () {
    $.unblockUI();
};


// Add things to the default namespace D:
Object.keys = Object.keys || function (o) {
    var result = [];
    for (var name in o) {
        if (o.hasOwnProperty(name))
            result.push(name);
    }
    return result;
};

String.prototype.reverse = function () {
    return this.split("").reverse().join("");
};

Array.prototype.sum = function (selector) {
    if (typeof selector !== 'function') {
        selector = function (item) {
            return item;
        }
    }
    var sum = 0;
    for (var i = 0; i < this.length; i++) {
        sum += selector(this[i]);
    }
    return sum;
};
Array.prototype.average = function (selector) {
    return this.sum(selector) / this.length;
};
