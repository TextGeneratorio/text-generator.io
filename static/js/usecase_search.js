// Simple search filter for use cases page
window.addEventListener('DOMContentLoaded', function () {
    var searchInput = document.getElementById('use-case-search');
    if (!searchInput) return;
    var items = document.querySelectorAll('#use-case-list .use-case-item');
    searchInput.addEventListener('input', function () {
        var filter = searchInput.value.toLowerCase();
        items.forEach(function (item) {
            var text = item.textContent.toLowerCase();
            if (text.indexOf(filter) === -1) {
                item.style.display = 'none';
            } else {
                item.style.display = '';
            }
        });
    });
});
