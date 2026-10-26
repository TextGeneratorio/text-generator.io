import { improvePrompt, promptModes } from './prompt-improver-recipes.mjs';
const form = document.getElementById('prompt-improver-form');
if (form) {
  const mode = document.getElementById('improver-mode');
  const output = document.getElementById('improver-output');
  const status = document.getElementById('improver-status');
  for (const item of promptModes) mode.add(new Option(item.label, item.id));
  mode.value = 'implement';
  const describe = () => { document.getElementById('improver-description').textContent = promptModes.find(item => item.id === mode.value).description; };
  mode.addEventListener('change', describe);
  describe();
  form.addEventListener('submit', event => {
    event.preventDefault();
    try {
      output.value = improvePrompt(document.getElementById('improver-input').value, mode.value, document.getElementById('improver-extra').value);
      document.getElementById('improver-result').hidden = false;
      status.textContent = 'Improved prompt ready. Review before using.';
    } catch (error) { status.textContent = error.message; }
  });
  document.getElementById('improver-copy').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(output.value); status.textContent = 'Copied.'; }
    catch { status.textContent = 'Clipboard unavailable. Select and copy the output manually.'; }
  });
}
