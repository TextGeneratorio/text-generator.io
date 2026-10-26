(() => {
  'use strict';

  const form = document.getElementById('prompt-opt-form');
  if (!form) return;

  const button = document.getElementById('optimize-btn');
  const buttonLabel = button.querySelector('[data-button-label]');
  const status = document.getElementById('prompt-opt-status');
  const resultPanel = document.getElementById('prompt-opt-result');
  const emptyPanel = document.getElementById('prompt-opt-empty');
  const finalPrompt = document.getElementById('final-prompt');
  const history = document.getElementById('prompt-opt-history');
  const copyButton = document.getElementById('copy-final-prompt');

  function setLoading(loading) {
    button.disabled = loading;
    button.classList.toggle('is-loading', loading);
    buttonLabel.textContent = loading ? 'Improving your prompt…' : 'Improve my prompt';
    if (loading) status.textContent = 'Comparing a few stronger versions…';
  }

  function displayScore(value) {
    const number = Number(value || 0);
    const normalized = number > 0 && number <= 1 ? number * 100 : number;
    return Math.max(0, Math.min(100, Math.round(normalized)));
  }

  function renderHistory(evaluations) {
    history.replaceChildren();
    (evaluations || []).forEach((evaluation, index) => {
      const item = document.createElement('li');
      const heading = document.createElement('div');
      const label = document.createElement('strong');
      const score = document.createElement('span');
      const feedback = document.createElement('p');
      label.textContent = index === 0 ? 'Starting prompt' : `Revision ${index}`;
      score.textContent = `${displayScore(evaluation.score)}/100`;
      feedback.textContent = evaluation.feedback || 'No additional feedback.';
      heading.append(label, score);
      item.append(heading, feedback);
      history.appendChild(item);
    });
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    setLoading(true);
    status.classList.remove('is-error');

    try {
      const response = await fetch('/api/v1/optimize-prompt', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          prompt: document.getElementById('initial-prompt').value.trim(),
          evolve_prompt: document.getElementById('evolve-prompt').value.trim(),
          judge_prompt: document.getElementById('judge-prompt').value.trim(),
          iterations: 2
        })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || 'We could not improve this prompt. Please try again.');
      if (!payload.final_prompt) throw new Error('The improved prompt came back empty. Please try again.');

      finalPrompt.textContent = payload.final_prompt;
      renderHistory(payload.evaluations);
      emptyPanel.hidden = true;
      resultPanel.hidden = false;
      status.textContent = 'Your improved prompt is ready.';
      resultPanel.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    } catch (error) {
      status.textContent = error.message || 'We could not improve this prompt. Please try again.';
      status.classList.add('is-error');
    } finally {
      setLoading(false);
    }
  });

  copyButton.addEventListener('click', async () => {
    await navigator.clipboard.writeText(finalPrompt.textContent || '');
    copyButton.innerHTML = '<span class="material-icons" aria-hidden="true">check</span> Copied';
    window.setTimeout(() => {
      copyButton.innerHTML = '<span class="material-icons" aria-hidden="true">content_copy</span> Copy';
    }, 1400);
  });
})();
