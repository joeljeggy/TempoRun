async function startrun() { try { await fetch("/set_command/start", { method: "GET" }); } catch (e) {} }
async function pauserun() { try { await fetch("/set_command/pause", { method: "GET" }); } catch (e) {} }
async function stoprun() { try { await fetch("/set_command/stop", { method: "GET" }); } catch (e) {} }
async function nextTrack() { try { await fetch("/player/next", { method: "POST" }); } catch (e) {} }
async function prevTrack() { try { await fetch("/player/previous", { method: "POST" }); } catch (e) {} }
async function playpause() { try { await fetch("/player/playpause", { method: "POST" }); } catch (e) {} }

async function refreshStatus() {
  let data;
  try {
    const res = await fetch("/status");
    data = await res.json();
  } catch (e) {
    return;
  }
  const t = data.treadmill;
  document.getElementById("status").textContent = t.status;
  document.getElementById("statSpeed").textContent = t.speed;
  document.getElementById("statDistance").textContent = t.distance.toFixed(2);
  document.getElementById("statTime").textContent = t.time;
  document.getElementById("statTarget").textContent = t.target;
  document.getElementById("statCalories").textContent = t.calories;

  const now = Date.now();
  if (!window._lastLocalCutoutChange || now - window._lastLocalCutoutChange > 500) {
    const sw = document.getElementById("dummySwitch");
    const input = document.getElementById("speedCutout");
    if (sw && typeof t.speed_cutout_enabled !== "undefined") {
      sw.checked = !!t.speed_cutout_enabled;
    }
    if (input && typeof t.speed_cutout_value !== "undefined") {
      input.value = t.speed_cutout_value;
    }
    updateSpeedCutoutEnabled();
  }

  const m = data.music;
  document.getElementById("currentSong").textContent = m.current;
  document.getElementById("nextSong").textContent = m.next;
  const curSp = document.getElementById("currentSpeed");
  const nxtSp = document.getElementById("nextSpeed");
  if (curSp) curSp.textContent = m.current_speed;
  if (nxtSp) nxtSp.textContent = m.next_speed;

  if (!window.__lastSongDisplayed || window.__lastSongDisplayed !== m.current) {
    const img = document.getElementById("coverArt");
    if (m.cover_url) {
      img.src = m.cover_url;
      img.style.display = "block";
    } else {
      img.src = "";
      img.style.display = "none";
    }
    window.__lastSongDisplayed = m.current;
  }
}

function adjustTime(delta) {
  const input = document.getElementById("timeMinutes");
  let val = parseInt(input.value, 10);
  if (isNaN(val)) val = 20;
  val += delta;
  if (val < 5) val = 5;
  if (val > 120) val = 120;
  input.value = val;
}

function adjustSpeedCutout(delta) {
  const input = document.getElementById("speedCutout");
  if (!input) return;
  let val = parseInt(input.value, 10);
  if (isNaN(val)) val = 10;
  val += delta;
  if (val < 1) val = 1;
  if (val > 20) val = 20;
  input.value = val;
  if (typeof pushSpeedCutout === "function") {
    pushSpeedCutout();
  }
}

async function generatePlaylist() {
  const btn = document.getElementById("genPlaylistBtn");
  const spinner = document.getElementById("genPlaylistSpinner");
  const text = document.getElementById("genPlaylistText");
  const minutesInput = document.getElementById("timeMinutes");
  let minutes = 20;
  if (minutesInput) {
    const m = parseInt(minutesInput.value, 10);
    if (!isNaN(m)) minutes = m;
  }
  minutes = Math.min(60, Math.max(5, minutes));
  btn.disabled = true;
  spinner.style.display = "inline-block";
  text.style.opacity = "0.5";
  try {
    const res = await fetch("/generate_playlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ time_seconds: minutes * 60 }),
    });
    const data = await res.json();
    if (data.status === "ok") {
      notify("Playlist generated and queued!");
    } else {
      alert("Error: " + (data.message || "Unknown error"));
    }
  } catch (e) {
    alert("Failed to generate playlist.");
  } finally {
    btn.disabled = false;
    spinner.style.display = "none";
    text.style.opacity = "1";
  }
}
setInterval(refreshStatus, 250);

async function pushSpeedCutout() {
  const sw = document.getElementById("dummySwitch");
  const input = document.getElementById("speedCutout");
  if (!sw || !input) return;
  window._lastLocalCutoutChange = Date.now();
  const payload = { enabled: sw.checked, value: parseInt(input.value || "0", 10) };
  try {
    await fetch("/speed_cutout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (e) {}
}

function updateSpeedCutoutEnabled() {
  const enabled = document.getElementById("dummySwitch").checked;
  const dec = document.getElementById("speedCutoutDec");
  const inc = document.getElementById("speedCutoutInc");
  const input = document.getElementById("speedCutout");
  [dec, inc, input].forEach((el) => {
    if (el) el.disabled = !enabled;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const sw = document.getElementById("dummySwitch");
  const input = document.getElementById("speedCutout");
  if (sw) {
    sw.addEventListener("change", () => {
      updateSpeedCutoutEnabled();
      pushSpeedCutout();
    });
    updateSpeedCutoutEnabled();
  }
  if (input) {
    input.addEventListener("input", () => {
      pushSpeedCutout();
    });
  }
  fetch("/speed_cutout")
    .then((r) => r.json())
    .then((s) => {
      if (sw) sw.checked = !!s.enabled;
      if (input) input.value = s.value;
      updateSpeedCutoutEnabled();
    })
    .catch(() => {});
});

function notify(message, duration = 3000) {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerHTML = `<span class="toast-icon">🎵</span>${message}`;
  container.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 50);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
