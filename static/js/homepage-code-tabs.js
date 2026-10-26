(function () {
    "use strict";

    function initializeCodeTabs(codeWindow) {
        var tabs = Array.prototype.slice.call(codeWindow.querySelectorAll("[data-code-tab]"));
        var panels = Array.prototype.slice.call(codeWindow.querySelectorAll("[data-code-panel]"));

        function selectTab(tab, moveFocus) {
            var language = tab.getAttribute("data-code-tab");

            tabs.forEach(function (item) {
                var isSelected = item === tab;
                item.classList.toggle("is-active", isSelected);
                item.setAttribute("aria-selected", String(isSelected));
                item.tabIndex = isSelected ? 0 : -1;
            });

            panels.forEach(function (panel) {
                panel.hidden = panel.getAttribute("data-code-panel") !== language;
            });

            if (moveFocus) {
                tab.focus();
            }
        }

        tabs.forEach(function (tab, index) {
            tab.addEventListener("click", function () {
                selectTab(tab, false);
            });

            tab.addEventListener("keydown", function (event) {
                var nextIndex;

                if (event.key === "ArrowRight") {
                    nextIndex = (index + 1) % tabs.length;
                } else if (event.key === "ArrowLeft") {
                    nextIndex = (index - 1 + tabs.length) % tabs.length;
                } else if (event.key === "Home") {
                    nextIndex = 0;
                } else if (event.key === "End") {
                    nextIndex = tabs.length - 1;
                } else {
                    return;
                }

                event.preventDefault();
                selectTab(tabs[nextIndex], true);
            });
        });
    }

    document.querySelectorAll(".tg-code-window").forEach(initializeCodeTabs);
})();
