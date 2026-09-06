'use strict';

const STORAGE_KEY = 'enabled';
const toggle = document.getElementById('enabled');
const status = document.getElementById('status');
const stateDescription = document.getElementById('state-description');

function render(enabled) {
  toggle.checked = enabled;
  status.textContent = enabled ? 'On' : 'Off';
  document.body.dataset.enabled = enabled ? 'true' : 'false';
  delete document.body.dataset.state;

  if (stateDescription) {
    stateDescription.textContent = enabled
      ? 'Rufus hidden · sidebar space reclaimed'
      : 'Amazon left untouched';
  }
}

async function initialize() {
  const stored = await chrome.storage.local.get({ [STORAGE_KEY]: true });
  render(stored[STORAGE_KEY] !== false);

  toggle.addEventListener('change', async () => {
    const enabled = toggle.checked;
    toggle.disabled = true;
    try {
      await chrome.storage.local.set({ [STORAGE_KEY]: enabled });
      render(enabled);
    } catch (error) {
      const current = await chrome.storage.local.get({ [STORAGE_KEY]: true });
      render(current[STORAGE_KEY] !== false);
      console.error('Failed to update suppressor preference.', error);
    } finally {
      toggle.disabled = false;
    }
  });
}

initialize().catch((error) => {
  toggle.disabled = true;
  status.textContent = 'Unavailable';
  document.body.dataset.state = 'error';
  if (stateDescription) stateDescription.textContent = 'Could not read the local setting';
  console.error('Failed to initialize suppressor preference.', error);
});
