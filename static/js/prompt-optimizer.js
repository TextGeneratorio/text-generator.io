document.getElementById('optimize-btn').addEventListener('click', async function() {
  const initial = document.getElementById('initial-prompt').value;
  const evolve = document.getElementById('evolve-prompt').value;
  const judge = document.getElementById('judge-prompt').value;
  const resp = await fetch('/api/v1/optimize-prompt', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: initial, evolve_prompt: evolve, judge_prompt: judge })
  });
  const data = await resp.json();
  document.getElementById('final-prompt').innerText = data.final_prompt;
  const tbody = document.getElementById('results-body');
  tbody.innerHTML = '';
  data.evaluations.forEach(ev => {
    const row = document.createElement('tr');
    const p = document.createElement('td');
    p.textContent = ev.prompt;
    row.appendChild(p);
    const j = document.createElement('td');
    j.textContent = ev.feedback;
    row.appendChild(j);
    const s = document.createElement('td');
    s.textContent = ev.score;
    row.appendChild(s);
    tbody.appendChild(row);
  });
});
