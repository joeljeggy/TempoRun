// Admin page JS: stride controls and clear queue

function notify(message, type = 'info') {
  // Reuse toast from main.js if present; otherwise basic alert fallback
  if (window.showToast) return window.showToast(message, type);
  console.log(`[${type}]`, message);
}

async function loadStride() {
  try {
    const res = await fetch('/api/stride');
    if (!res.ok) throw new Error('Failed to load stride');
    const data = await res.json();
    const { walk_sl, sprint_sl, run_sl } = data;
    document.getElementById('walk_sl').value = walk_sl.toFixed(2);
    document.getElementById('sprint_sl').value = sprint_sl.toFixed(2);
    document.getElementById('run_sl').value = run_sl.toFixed(2);
  } catch (e) {
    notify('Error loading stride settings', 'error');
  }
}

async function saveStride() {
  const walk = parseFloat(document.getElementById('walk_sl').value);
  const sprint = parseFloat(document.getElementById('sprint_sl').value);
  const run = parseFloat(document.getElementById('run_sl').value);
  try {
    const res = await fetch('/api/stride', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ walk_sl: walk, sprint_sl: sprint, run_sl: run })
    });
    if (!res.ok) throw new Error('Failed to save stride');
    const data = await res.json();
    document.getElementById('walk_sl').value = data.walk_sl.toFixed(2);
    document.getElementById('sprint_sl').value = data.sprint_sl.toFixed(2);
    document.getElementById('run_sl').value = data.run_sl.toFixed(2);
    notify('Stride settings saved');
  } catch (e) {
    notify('Error saving stride settings', 'error');
  }
}

function adjustStride(which, delta) {
  const el = document.getElementById(which);
  const cur = parseFloat(el.value || '0');
  let next = cur + delta;
  // clamp based on field
  let min = 0.3, max = 2.5;
  if (which === 'walk_sl' || which === 'sprint_sl') max = 1.5;
  next = Math.max(min, Math.min(max, next));
  el.value = next.toFixed(2);
  // autosave on step change
  saveStride();
}

async function clearQueue() {
  try {
    const res = await fetch('/api/clear_queue', { method: 'POST' });
    if (!res.ok) throw new Error('Failed to clear queue');
    notify('Queued a clear-queue command');
  } catch (e) {
    notify('Error clearing queue', 'error');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  loadStride();
  // Save on manual edits blur
  ['walk_sl','sprint_sl','run_sl'].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener('change', () => saveStride());
  });
});
