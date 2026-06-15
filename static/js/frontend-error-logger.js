(function () {
    "use strict";

    var endpoint = "/api/frontend-error";
    var maxEventsPerPage = 20;
    var sentEvents = 0;
    var nativeFetch = window.fetch ? window.fetch.bind(window) : null;
    var sourceMapHintsPromise = null;
    var browserExtensionUrlRe = /\b(?:chrome|moz|safari|ms-browser)-extension:\/\//i;

    function sameOrigin(url) {
        try {
            return new URL(url, window.location.href).origin === window.location.origin;
        } catch (_error) {
            return false;
        }
    }

    function truncate(value, maxLength) {
        if (value === undefined || value === null) {
            return value;
        }
        var text = String(value);
        if (text.length <= maxLength) {
            return text;
        }
        return text.slice(0, maxLength) + "...[truncated]";
    }

    function serializeError(error) {
        if (!error) {
            return {};
        }
        return {
            name: truncate(error.name || "Error", 200),
            message: truncate(error.message || String(error), 2000),
            stack: truncate(error.stack || "", 12000)
        };
    }

    function containsBrowserExtensionUrl(value) {
        if (value === undefined || value === null) {
            return false;
        }
        if (typeof value === "string") {
            return browserExtensionUrlRe.test(value);
        }
        try {
            return browserExtensionUrlRe.test(JSON.stringify(value));
        } catch (_error) {
            return false;
        }
    }

    function sourceMapUrlFromScriptText(scriptUrl, scriptText) {
        var matches = scriptText.match(/[#@]\s*sourceMappingURL=([^\s]+)/g);
        if (!matches || !matches.length) {
            return null;
        }
        var last = matches[matches.length - 1].replace(/^[#@]\s*sourceMappingURL=/, "");
        try {
            return new URL(last, scriptUrl).href;
        } catch (_error) {
            return last;
        }
    }

    function guessedSourceMapUrl(scriptUrl) {
        if (/\.min\.js(?:\?|#|$)/.test(scriptUrl)) {
            return scriptUrl.replace(/\.min\.js(\?|#|$)/, ".min.js.map$1");
        }
        return null;
    }

    function collectSourceMapHints() {
        if (sourceMapHintsPromise) {
            return sourceMapHintsPromise;
        }
        if (!nativeFetch) {
            sourceMapHintsPromise = Promise.resolve([]);
            return sourceMapHintsPromise;
        }

        var scripts = Array.prototype.slice.call(document.scripts)
            .map(function (script) { return script.src; })
            .filter(function (src) { return src; })
            .slice(-12);

        sourceMapHintsPromise = Promise.all(scripts.map(function (src) {
            if (!sameOrigin(src)) {
                return Promise.resolve({
                    scriptUrl: src,
                    sourceMapUrl: guessedSourceMapUrl(src)
                });
            }

            return nativeFetch(src, { credentials: "same-origin" })
                .then(function (response) {
                    if (!response.ok) {
                        return null;
                    }
                    return response.text();
                })
                .then(function (text) {
                    if (!text) {
                        return null;
                    }
                    return {
                        scriptUrl: src,
                        sourceMapUrl: sourceMapUrlFromScriptText(src, text.slice(-8000)) || guessedSourceMapUrl(src)
                    };
                })
                .catch(function () {
                    return {
                        scriptUrl: src,
                        sourceMapUrl: guessedSourceMapUrl(src)
                    };
                });
        })).then(function (items) {
            return items.filter(function (item) { return item && item.sourceMapUrl; });
        });

        return sourceMapHintsPromise;
    }

    function postEvent(event) {
        if (containsBrowserExtensionUrl(event)) {
            return;
        }
        if (sentEvents >= maxEventsPerPage) {
            return;
        }
        sentEvents += 1;

        collectSourceMapHints().then(function (sourceMaps) {
            var payload = {
                event: event,
                page: {
                    url: window.location.href,
                    referrer: document.referrer || "",
                    title: document.title || "",
                    userAgent: navigator.userAgent || "",
                    timestamp: new Date().toISOString()
                },
                sourceMaps: sourceMaps
            };
            var body = JSON.stringify(payload);

            if (navigator.sendBeacon) {
                var blob = new Blob([body], { type: "application/json" });
                if (navigator.sendBeacon(endpoint, blob)) {
                    return;
                }
            }

            if (nativeFetch) {
                nativeFetch(endpoint, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: body,
                    keepalive: true,
                    credentials: "same-origin"
                }).catch(function () {});
            }
        });
    }

    window.addEventListener("error", function (event) {
        if (event.target && event.target !== window) {
            postEvent({
                type: "resource_error",
                tagName: event.target.tagName || "",
                sourceUrl: event.target.src || event.target.href || "",
                outerHTML: truncate(event.target.outerHTML || "", 1000)
            });
            return;
        }

        postEvent({
            type: "window_error",
            message: truncate(event.message || "", 2000),
            filename: event.filename || "",
            lineno: event.lineno || null,
            colno: event.colno || null,
            error: serializeError(event.error)
        });
    }, true);

    window.addEventListener("unhandledrejection", function (event) {
        postEvent({
            type: "unhandledrejection",
            reason: serializeError(event.reason),
            message: truncate(event.reason && event.reason.message ? event.reason.message : event.reason, 2000)
        });
    });

    if (nativeFetch) {
        window.fetch = function () {
            var args = arguments;
            var requestUrl = "";
            try {
                requestUrl = typeof args[0] === "string" ? args[0] : args[0].url;
            } catch (_error) {}

            return nativeFetch.apply(null, args).then(function (response) {
                if (response && response.status >= 500 && requestUrl.indexOf(endpoint) === -1) {
                    postEvent({
                        type: "fetch_5xx",
                        url: response.url || requestUrl,
                        status: response.status,
                        statusText: response.statusText || ""
                    });
                }
                return response;
            }).catch(function (error) {
                if (requestUrl.indexOf(endpoint) === -1) {
                    postEvent({
                        type: "fetch_exception",
                        url: requestUrl,
                        error: serializeError(error)
                    });
                }
                throw error;
            });
        };
    }
})();
