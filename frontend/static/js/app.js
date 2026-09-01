/**
 * Main Application Logic & Event Handling
 */

let statsInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  startStatsPolling();
  loadUploadedVideosList();
  loadReportsData();
});

// Tab navigation
function switchTab(tabId) {
  const tabs = ['live', 'analytics', 'reports', 'settings'];
  tabs.forEach(t => {
    const view = document.getElementById(`view-${t}`);
    const btn = document.getElementById(`tab-${t}`);
    if (t === tabId) {
      view.classList.remove('hidden');
      btn.classList.add('border-cyan-400', 'text-cyan-400');
      btn.classList.remove('border-transparent', 'text-gray-400');
    } else {
      view.classList.add('hidden');
      btn.classList.remove('border-cyan-400', 'text-cyan-400');
      btn.classList.add('border-transparent', 'text-gray-400');
    }
  });

  if (tabId === 'analytics') {
    loadAnalyticsData();
  } else if (tabId === 'reports') {
    loadReportsData();
  }
}

// Live Statistics Polling
function startStatsPolling() {
  if (statsInterval) clearInterval(statsInterval);
  statsInterval = setInterval(fetchLiveStats, 600);
}

async function fetchLiveStats() {
  try {
    const res = await fetch('/api/stream/stats');
    if (!res.ok) return;
    const stats = await res.json();

    // Update Top Counters
    document.getElementById('stat-total-in').textContent = stats.total_in;
    document.getElementById('stat-total-out').textContent = stats.total_out;
    document.getElementById('stat-total-count').textContent = stats.total_count;
    document.getElementById('stat-fps').textContent = stats.fps.toFixed(1);
    document.getElementById('header-fps').textContent = stats.fps.toFixed(1);
    document.getElementById('header-tracks').textContent = stats.active_tracks_count;

    // Status indicator
    const ping = document.getElementById('status-ping');
    const dot = document.getElementById('status-dot');
    const txt = document.getElementById('status-text');

    if (stats.is_active) {
      ping.className = "animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75";
      dot.className = "relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500";
      txt.textContent = `Streaming (${stats.fps.toFixed(1)} FPS)`;
      document.getElementById('stream-fallback').classList.add('hidden');
    } else {
      ping.className = "hidden";
      dot.className = "relative inline-flex rounded-full h-2.5 w-2.5 bg-gray-500";
      txt.textContent = "Pipeline Idle";
    }

    // Update Category Cards
    const cats = stats.class_counts || {};
    const getCatTotal = (c) => cats[c] ? cats[c].TOTAL : 0;

    document.getElementById('cat-person').textContent = getCatTotal('person');
    document.getElementById('cat-car').textContent = getCatTotal('car');
    document.getElementById('cat-bus').textContent = getCatTotal('bus');
    document.getElementById('cat-truck').textContent = getCatTotal('truck');
    document.getElementById('cat-motorcycle').textContent = getCatTotal('motorcycle');
    document.getElementById('cat-bicycle').textContent = getCatTotal('bicycle');

    // Update Recent Events Ticker
    renderEventsTicker(stats.recent_events);
  } catch (err) {
    console.debug("Error polling stats:", err);
  }
}

function renderEventsTicker(events) {
  const container = document.getElementById('events-container');
  if (!events || events.length === 0) {
    return;
  }

  container.innerHTML = events.slice(0, 15).map(ev => {
    const isDown = ev.direction === 'IN';
    const badgeClass = isDown ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30';
    const icon = isDown ? 'fa-arrow-down' : 'fa-arrow-up';
    const classIcon = getClassIcon(ev.class_name);
    const timeStr = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '';

    return `
      <div class="p-2 bg-dark-900/80 rounded-lg border border-gray-800 flex items-center justify-between animate-fadeIn">
        <div class="flex items-center space-x-2">
          <span class="text-xs px-2 py-0.5 rounded font-bold uppercase ${badgeClass}">
            <i class="fa-solid ${icon} mr-1"></i>${ev.direction}
          </span>
          <span class="font-semibold text-gray-200 capitalize flex items-center gap-1.5">
            <i class="fa-solid ${classIcon} text-indigo-400"></i> ${ev.class_name}
          </span>
          <span class="text-[10px] text-gray-500 font-mono">#${ev.track_id}</span>
        </div>
        <div class="text-[10px] text-gray-400 font-mono">${timeStr}</div>
      </div>
    `;
  }).join('');
}

function getClassIcon(className) {
  const mapping = {
    person: 'fa-person',
    car: 'fa-car',
    bus: 'fa-bus',
    truck: 'fa-truck',
    motorcycle: 'fa-motorcycle',
    bicycle: 'fa-bicycle'
  };
  return mapping[className] || 'fa-tag';
}

// Video Feed Controls
async function startStream() {
  const source = document.getElementById('select-source').value;
  const videoId = document.getElementById('select-uploaded-video').value;
  const webcamIdx = document.getElementById('input-webcam-idx').value || 0;
  const conf = parseFloat(document.getElementById('slider-conf').value) || 0.35;

  const payload = {
    source_type: source,
    video_id: videoId ? parseInt(videoId) : null,
    webcam_index: parseInt(webcamIdx),
    confidence_threshold: conf,
    iou_threshold: 0.45,
    line_config: getLineConfigPayload()
  };

  try {
    const res = await fetch('/api/stream/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      // Reload stream image
      const streamImg = document.getElementById('video-stream');
      streamImg.src = `/api/stream/feed?t=${Date.now()}`;
      document.getElementById('stream-fallback').classList.add('hidden');
    }
  } catch (err) {
    console.error("Error starting stream:", err);
  }
}

async function stopStream() {
  try {
    await fetch('/api/stream/stop', { method: 'POST' });
    document.getElementById('stream-fallback').classList.remove('hidden');
  } catch (err) {
    console.error("Error stopping stream:", err);
  }
}

async function resetCounters() {
  try {
    await fetch('/api/stream/reset-counts', { method: 'POST' });
    fetchLiveStats();
  } catch (err) {
    console.error("Error resetting counts:", err);
  }
}

async function updateConfidence(val) {
  document.getElementById('label-conf').textContent = parseFloat(val).toFixed(2);
  try {
    await fetch(`/api/stream/confidence?conf=${val}`, { method: 'POST' });
  } catch (err) {
    console.error("Error updating confidence:", err);
  }
}

async function toggleVisuals() {
  const boxes = document.getElementById('toggle-boxes').checked;
  const trails = document.getElementById('toggle-trails').checked;
  const line = document.getElementById('toggle-line').checked;
  const hud = document.getElementById('toggle-hud').checked;

  try {
    await fetch(`/api/stream/toggle?boxes=${boxes}&trails=${trails}&line=${line}&hud=${hud}`, { method: 'POST' });
  } catch (err) {
    console.error("Error updating visuals:", err);
  }
}

function handleStreamError() {
  document.getElementById('stream-fallback').classList.remove('hidden');
}

// Source selection UI changes
function onSourceChange() {
  const source = document.getElementById('select-source').value;
  const uploadBox = document.getElementById('upload-box');
  const webcamBox = document.getElementById('webcam-box');
  const badge = document.getElementById('active-source-badge');

  uploadBox.classList.add('hidden');
  webcamBox.classList.add('hidden');

  if (source === 'upload') {
    uploadBox.classList.remove('hidden');
    badge.textContent = "Uploaded File";
  } else if (source === 'webcam') {
    webcamBox.classList.remove('hidden');
    badge.textContent = "Webcam Stream";
  } else {
    badge.textContent = "Sample Simulation";
  }
}

function applySourceChange() {
  startStream();
}

// Video Upload Handler
async function uploadSelectedVideo(input) {
  if (!input.files || input.files.length === 0) return;
  const file = input.files[0];

  const formData = new FormData();
  formData.append('file', file);

  const progBar = document.getElementById('upload-progress-bar');
  const prog = document.getElementById('upload-progress');
  progBar.classList.remove('hidden');
  prog.style.width = '30%';

  try {
    const res = await fetch('/api/videos/upload', {
      method: 'POST',
      body: formData
    });
    prog.style.width = '100%';
    setTimeout(() => progBar.classList.add('hidden'), 800);

    if (res.ok) {
      const data = await res.json();
      alert(`Video '${file.name}' uploaded successfully!`);
      await loadUploadedVideosList();
      document.getElementById('select-uploaded-video').value = data.video.id;
    } else {
      const err = await res.json();
      alert(`Upload error: ${err.detail}`);
    }
  } catch (err) {
    console.error("Error uploading video:", err);
    alert("Upload failed. Check server console.");
  }
}

async function loadUploadedVideosList() {
  try {
    const res = await fetch('/api/videos');
    if (!res.ok) return;
    const videos = await res.json();
    const select = document.getElementById('select-uploaded-video');
    if (videos.length === 0) {
      select.innerHTML = `<option value="">No uploaded videos yet</option>`;
      return;
    }
    select.innerHTML = videos.map(v => `
      <option value="${v.id}">${v.filename} (${v.width}x${v.height}, ${v.duration.toFixed(1)}s)</option>
    `).join('');
  } catch (err) {
    console.error("Error loading videos list:", err);
  }
}

// Virtual Line Calibration & Presets
function updateLineCoordsUI() {
  const sx = parseFloat(document.getElementById('input-start-x').value);
  const sy = parseFloat(document.getElementById('input-start-y').value);
  const ex = parseFloat(document.getElementById('input-end-x').value);
  const ey = parseFloat(document.getElementById('input-end-y').value);

  document.getElementById('val-start-x').textContent = sx.toFixed(2);
  document.getElementById('val-start-y').textContent = sy.toFixed(2);
  document.getElementById('val-end-x').textContent = ex.toFixed(2);
  document.getElementById('val-end-y').textContent = ey.toFixed(2);
}

function applyLinePreset(sx, sy, ex, ey) {
  document.getElementById('input-start-x').value = sx;
  document.getElementById('input-start-y').value = sy;
  document.getElementById('input-end-x').value = ex;
  document.getElementById('input-end-y').value = ey;
  updateLineCoordsUI();
  saveLineConfiguration();
}

function getLineConfigPayload() {
  return {
    line_start_x: parseFloat(document.getElementById('input-start-x').value),
    line_start_y: parseFloat(document.getElementById('input-start-y').value),
    line_end_x: parseFloat(document.getElementById('input-end-x').value),
    line_end_y: parseFloat(document.getElementById('input-end-y').value),
    direction_mode: document.getElementById('input-direction-mode').value
  };
}

async function saveLineConfiguration() {
  const payload = getLineConfigPayload();
  try {
    const res = await fetch('/api/stream/line-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("Virtual line calibrated and applied!");
    }
  } catch (err) {
    console.error("Error saving line config:", err);
  }
}

// Historical Reports Table
async function loadReportsData() {
  try {
    const res = await fetch('/api/analytics/summary');
    if (!res.ok) return;
    const data = await res.json();
    const tbody = document.getElementById('reports-table-body');

    if (!data.recent_crossings || data.recent_crossings.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-4 py-8 text-center text-gray-500">No crossing records logged yet. Run the live stream to accumulate data.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.recent_crossings.map(r => {
      const isDown = r.direction === 'IN';
      const badge = isDown ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30';
      const icon = getClassIcon(r.class_name);
      return `
        <tr class="hover:bg-dark-700/50 transition">
          <td class="px-4 py-3 font-mono text-gray-400">#${r.id}</td>
          <td class="px-4 py-3 font-mono text-cyan-400">Track #${r.track_id}</td>
          <td class="px-4 py-3 font-semibold text-white capitalize"><i class="fa-solid ${icon} mr-1.5 text-indigo-400"></i>${r.class_name}</td>
          <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-[11px] font-bold uppercase ${badge}">${r.direction}</span></td>
          <td class="px-4 py-3 text-gray-400">primary_line</td>
          <td class="px-4 py-3 font-mono text-gray-400">${new Date(r.crossing_time).toLocaleString()}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error("Error loading reports:", err);
  }
}
