(function () {
    function noop() {}

    if (!window.hljs) {
        window.hljs = {
            highlightAll: noop,
            highlightBlock: noop,
            highlightElement: noop
        };
        return;
    }

    if (typeof window.hljs.highlightElement !== 'function' && typeof window.hljs.highlightBlock === 'function') {
        window.hljs.highlightElement = function (block) {
            window.hljs.highlightBlock(block);
        };
    }

    if (typeof window.hljs.highlightAll !== 'function') {
        window.hljs.highlightAll = function () {
            var blocks = document.querySelectorAll('pre code');
            for (var i = 0; i < blocks.length; i += 1) {
                window.hljs.highlightElement(blocks[i]);
            }
        };
    }
})();
