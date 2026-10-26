(() => {
  'use strict';

  const form = document.getElementById('domain-search-form');
  if (!form) return;

  const els = {
    brief: document.getElementById('domain-brief'),
    ideas: document.getElementById('domain-ideas'),
    batch: document.getElementById('domain-batch-size'),
    submit: document.getElementById('domain-search-submit'),
    workspace: document.getElementById('domain-workspace'),
    empty: document.getElementById('domain-empty-state'),
    content: document.getElementById('domain-results-content'),
    grid: document.getElementById('domain-results-grid'),
    loading: document.getElementById('domain-loading'),
    error: document.getElementById('domain-error'),
    more: document.getElementById('domain-explore-more'),
    wave: document.getElementById('domain-wave-badge'),
    waveNumber: document.querySelector('#domain-wave-badge span'),
    title: document.getElementById('domain-results-title'),
    copyAvailable: document.getElementById('domain-copy-available'),
    shortlist: document.getElementById('domain-shortlist'),
    shortlistEmpty: document.getElementById('domain-shortlist-empty'),
    download: document.getElementById('domain-download-shortlist'),
    noResults: document.getElementById('domain-no-filter-results'),
    countAll: document.getElementById('domain-count-all'),
    countAvailable: document.getElementById('domain-count-available'),
    countShortlisted: document.getElementById('domain-count-shortlisted')
  };

  const state = {
    domains: new Map(),
    shortlisted: new Set(readShortlist()),
    wave: 0,
    filter: 'all',
    loading: false
  };

  function readShortlist() {
    try {
      const value = JSON.parse(localStorage.getItem('tg-domain-shortlist') || '[]');
      return Array.isArray(value) ? value.filter(item => typeof item === 'string').slice(0, 80) : [];
    } catch (_) { return []; }
  }

  function saveShortlist() {
    localStorage.setItem('tg-domain-shortlist', JSON.stringify([...state.shortlisted]));
  }

  function parseIdeas() {
    return els.ideas.value.split(/[\n,]+/).map(value => value.trim()).filter(Boolean).slice(0, 30);
  }

  function setLoading(loading) {
    state.loading = loading;
    els.loading.hidden = !loading;
    els.submit.disabled = loading;
    els.more.disabled = loading;
    els.submit.querySelector('span:nth-child(2)').textContent = loading ? 'Exploring…' : 'Explore domains';
    if (loading) els.error.hidden = true;
  }

  function escapeHtml(value) {
    const node = document.createElement('div');
    node.textContent = String(value || '');
    return node.innerHTML;
  }

  function visibleDomains() {
    const values = [...state.domains.values()];
    if (state.filter === 'available') return values.filter(item => item.status === 'available');
    if (state.filter === 'shortlisted') return values.filter(item => state.shortlisted.has(item.domain));
    return values;
  }

  function render() {
    const all = [...state.domains.values()];
    const visible = visibleDomains();
    const available = all.filter(item => item.status === 'available').length;
    els.countAll.textContent = all.length;
    els.countAvailable.textContent = available;
    els.countShortlisted.textContent = state.shortlisted.size;
    els.title.textContent = all.length ? `${available} likely available from ${all.length} names` : 'Your next domain is a branch away.';
    els.wave.hidden = !state.wave;
    els.waveNumber.textContent = state.wave;
    els.more.hidden = !all.length;
    els.noResults.hidden = visible.length > 0;

    els.grid.innerHTML = visible.map(item => {
      const saved = state.shortlisted.has(item.domain);
      const status = ['available', 'taken', 'unknown'].includes(item.status) ? item.status : 'unknown';
      return `<article class="domain-card" data-domain="${escapeHtml(item.domain)}">
        <div class="domain-card-top">
          <div><h3 class="domain-card-name">${escapeHtml(item.domain)}</h3><span class="domain-status domain-status--${status}">${status}</span></div>
          <button class="domain-save${saved ? ' is-saved' : ''}" type="button" data-save title="${saved ? 'Remove from' : 'Add to'} shortlist" aria-label="${saved ? 'Remove from' : 'Add to'} shortlist">
            <span class="material-icons" aria-hidden="true">${saved ? 'bookmark' : 'bookmark_border'}</span>
          </button>
        </div>
        <p class="domain-card-copy">${escapeHtml(item.why)}</p>
        <div class="domain-card-footer">
          <span class="domain-strategy">${escapeHtml(item.strategy)}</span>
          <button class="domain-branch" type="button" data-branch>More like this →</button>
        </div>
      </article>`;
    }).join('');
    renderShortlist();
  }

  function renderShortlist() {
    const names = [...state.shortlisted];
    els.shortlistEmpty.hidden = names.length > 0;
    els.download.disabled = names.length === 0;
    els.shortlist.innerHTML = names.map(domain => `<li><span>${escapeHtml(domain)}</span><button type="button" data-remove="${escapeHtml(domain)}" aria-label="Remove ${escapeHtml(domain)}">×</button></li>`).join('');
  }

  async function runSearch(inspiration = '') {
    if (state.loading || !form.reportValidity()) return;
    els.empty.hidden = true;
    els.content.hidden = false;
    setLoading(true);
    if (state.domains.size) els.grid.innerHTML = '';

    try {
      const response = await fetch(form.dataset.endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          description: els.brief.value.trim(),
          current_ideas: parseIdeas(),
          exclude_domains: [...state.domains.keys()],
          inspiration,
          batch_size: Number(els.batch.value)
        })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || 'We could not finish that search. Please try again.');
      (payload.domains || []).forEach(item => state.domains.set(item.domain, item));
      state.wave += 1;
      render();
      if (inspiration) els.title.textContent = `Fresh branches from ${inspiration}`;
      els.workspace.scrollIntoView({behavior: 'smooth', block: 'start'});
    } catch (error) {
      els.error.textContent = error.message || 'We could not finish that search. Please try again.';
      els.error.hidden = false;
      render();
    } finally {
      setLoading(false);
    }
  }

  form.addEventListener('submit', event => { event.preventDefault(); runSearch(); });
  document.querySelectorAll('[data-start-search]').forEach(button => button.addEventListener('click', () => runSearch()));
  els.more.addEventListener('click', () => {
    const seeds = [...state.shortlisted].slice(0, 3);
    runSearch(seeds.length ? seeds.join(', ') : 'Diversify the strongest available directions');
  });

  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('is-active', item === button));
    render();
  }));

  els.grid.addEventListener('click', event => {
    const card = event.target.closest('.domain-card');
    if (!card) return;
    const domain = card.dataset.domain;
    if (event.target.closest('[data-save]')) {
      state.shortlisted.has(domain) ? state.shortlisted.delete(domain) : state.shortlisted.add(domain);
      saveShortlist(); render();
    } else if (event.target.closest('[data-branch]')) {
      runSearch(domain);
    }
  });

  els.shortlist.addEventListener('click', event => {
    const button = event.target.closest('[data-remove]');
    if (!button) return;
    state.shortlisted.delete(button.dataset.remove);
    saveShortlist(); render();
  });

  els.copyAvailable.addEventListener('click', async () => {
    const domains = [...state.domains.values()].filter(item => item.status === 'available').map(item => item.domain);
    if (!domains.length) return;
    await navigator.clipboard.writeText(domains.join('\n'));
    const original = els.copyAvailable.querySelector('span:last-child').textContent;
    els.copyAvailable.querySelector('span:last-child').textContent = 'Copied';
    window.setTimeout(() => { els.copyAvailable.querySelector('span:last-child').textContent = original; }, 1200);
  });

  els.download.addEventListener('click', () => {
    const blob = new Blob([[...state.shortlisted].join('\n') + '\n'], {type: 'text/plain'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'domain-shortlist.txt';
    link.click();
    URL.revokeObjectURL(link.href);
  });

  renderShortlist();
})();
