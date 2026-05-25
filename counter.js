async function updateCounter() {
  try {
    const ipRes = await fetch('https://api.ipify.org?format=json');
    const ipData = await ipRes.json();
    const res = await fetch(`/api/counter?ip=${ipData.ip}`);
    const data = await res.json();
    document.getElementById('counter').textContent = data.count;
  } catch(e) {
    document.getElementById('counter').textContent = '—';
  }
}

async function loadVisits() {
  try {
    const res = await fetch('/api/visits');
    const data = await res.json();

    // Recent visitors list
    const list = document.getElementById('visitor-list');
    if (data.recent.length === 0) {
      list.textContent = 'No visits yet';
    } else {
      list.innerHTML = data.recent.slice(0, 5).map(v =>
        `<div>${getFlagEmoji(v.countryCode)} ${v.city}, ${v.country}</div>`
      ).join('');
    }

    // Country breakdown
    const counts = document.getElementById('country-counts');
    if (data.countries.length > 0) {
      counts.innerHTML = data.countries
        .sort((a,b) => b.visits - a.visits)
        .slice(0, 4)
        .map(c => `<div style="display:flex;justify-content:space-between;gap:12px;">
          <span>${getFlagEmoji(c.countryCode)} ${c.country}</span>
          <span style="color:#00e5ff;">${c.visits}</span>
        </div>`).join('');
    }
  } catch(e) {
    document.getElementById('visitor-list').textContent = 'Unavailable';
  }
}

function getFlagEmoji(code) {
  if (!code || code === '??') return '🌍';
  return code.toUpperCase().replace(/./g, c =>
    String.fromCodePoint(127397 + c.charCodeAt())
  );
}

updateCounter();
loadVisits();