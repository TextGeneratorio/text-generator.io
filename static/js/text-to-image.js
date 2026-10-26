(function () {
    "use strict";

    var form = document.getElementById("tti-form");
    if (!form) return;

    var prompt = document.getElementById("tti-prompt");
    var count = document.getElementById("tti-count");
    var button = document.getElementById("tti-generate");
    var status = document.getElementById("tti-status");
    var empty = document.getElementById("tti-empty");
    var image = document.getElementById("tti-image");
    var actions = document.getElementById("tti-actions");
    var open = document.getElementById("tti-open");

    function updateCount() {
        count.textContent = prompt.value.length + " / 2000";
    }

    document.querySelectorAll("[data-prompt]").forEach(function (starter) {
        starter.addEventListener("click", function () {
            prompt.value = starter.getAttribute("data-prompt");
            updateCount();
            prompt.focus();
        });
    });

    prompt.addEventListener("input", updateCount);
    updateCount();

    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        status.classList.remove("is-error");
        status.textContent = "Generating on Netwrck Fast SDXL…";
        button.disabled = true;

        try {
            var response = await fetch("/api/tools/text-to-image/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: prompt.value,
                    size: form.querySelector("input[name=size]:checked").value
                })
            });
            var data = await response.json().catch(function () { return {}; });
            if (!response.ok) throw new Error(data.detail || "Image generation failed.");

            image.src = data.image_url;
            image.hidden = false;
            empty.hidden = true;
            actions.hidden = false;
            open.href = data.image_url;
            status.textContent = "Generated with " + data.model + " at " + data.size + ".";
        } catch (error) {
            status.classList.add("is-error");
            status.textContent = error.message;
            if (/log in/i.test(error.message)) {
                status.innerHTML = '<a href="/login?next=%2Ftools%2Ftext-to-image">Log in</a> to generate images.';
            }
        } finally {
            button.disabled = false;
        }
    });
})();
