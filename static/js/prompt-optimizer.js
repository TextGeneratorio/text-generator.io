document.addEventListener('DOMContentLoaded', async function () {
  const btn = document.getElementById('optimize-btn');
  if (!btn) return;
  
  // Check subscription status on page load
  const isSubscribed = await isUserSubscribed();
  
  if (!isSubscribed) {
    // User is not subscribed, disable the tool
    btn.disabled = true;
    btn.textContent = 'Premium Feature - Subscribe to Access';
    btn.addEventListener('click', function() {
      if (window.subscriptionModal) { window.subscriptionModal.show(); }
    });
    return;
  }
  
  btn.addEventListener('click', async function () {
    const initial = document.getElementById('initial-prompt').value;
    const evolve = document.getElementById('evolve-prompt').value;
    const judge = document.getElementById('judge-prompt').value;
    
    // Disable button and show loading state
    btn.disabled = true;
    btn.textContent = 'Optimizing...';
    
    try {
      const resp = await fetch('/api/v1/optimize-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: initial, evolve_prompt: evolve, judge_prompt: judge })
      });
      
      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${errorText}`);
      }
      
      const data = await resp.json();
      
      // Check if response has expected structure
      if (!data.final_prompt) {
        throw new Error('Invalid response: missing final_prompt');
      }
      
      document.getElementById('final-prompt').innerText = data.final_prompt;
      const tbody = document.getElementById('results-body');
      tbody.innerHTML = '';
      
      // Check if evaluations exist and is an array
      if (data.evaluations && Array.isArray(data.evaluations)) {
        data.evaluations.forEach(ev => {
          const row = document.createElement('tr');
          const p = document.createElement('td');
          p.textContent = ev.prompt || '';
          row.appendChild(p);
          const j = document.createElement('td');
          j.textContent = ev.feedback || '';
          row.appendChild(j);
          const s = document.createElement('td');
          s.textContent = ev.score || '';
          row.appendChild(s);
          tbody.appendChild(row);
        });
      }
    } catch (error) {
      console.error('Error optimizing prompt:', error);
      document.getElementById('final-prompt').innerText = `Error: ${error.message}`;
      const tbody = document.getElementById('results-body');
      tbody.innerHTML = '<tr><td colspan="3">Failed to optimize prompt. Please try again.</td></tr>';
    } finally {
      // Re-enable button
      btn.disabled = false;
      btn.textContent = 'Optimize';
    }
  });
});
