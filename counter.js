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
updateCounter();