(function () {
    const root = document.getElementById('marketing-workflow-tool');
    if (!root) return;

    const workflow = root.dataset.workflow || '';
    const runBtn = document.getElementById('run-workflow-btn');
    const status = document.getElementById('workflow-status');
    const output = document.getElementById('workflow-output');
    const outputText = document.getElementById('workflow-output-text');

    const targetUrlInput = document.getElementById('tool-target-url');
    const competitorsInput = document.getElementById('tool-competitors');
    const contextInput = document.getElementById('tool-context');

    function setStatus(text, isError) {
        if (!status) return;
        status.textContent = text || '';
        status.style.color = isError ? '#d32f2f' : '#666';
    }

    async function runWorkflow() {
        const targetUrl = targetUrlInput ? targetUrlInput.value.trim() : '';
        const competitors = (competitorsInput ? competitorsInput.value : '')
            .split('\n')
            .map((v) => v.trim())
            .filter(Boolean);
        const context = contextInput ? contextInput.value.trim() : '';

        setStatus('Running analysis...', false);
        if (runBtn) runBtn.disabled = true;

        try {
            const response = await fetch('/api/tools/marketing-workflow', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    workflow,
                    target_url: targetUrl,
                    competitor_urls: competitors,
                    business_context: context
                })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || data.error || 'Workflow request failed');
            }

            if (output && outputText) {
                outputText.textContent = data.combined_markdown || 'No output received.';
                output.style.display = 'block';
            }
            setStatus(`Done (${(data.analyses || []).length} model(s))`, false);
        } catch (error) {
            console.error('Workflow tool error:', error);
            setStatus(error.message || 'Failed to run workflow', true);
        } finally {
            if (runBtn) runBtn.disabled = false;
        }
    }

    if (runBtn) {
        runBtn.addEventListener('click', runWorkflow);
    }
})();
