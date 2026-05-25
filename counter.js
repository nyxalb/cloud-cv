async function updateCounter() {
  try {
    // Step 1: Get visitor's IP
    const ipRes = await fetch('https://api.ipify.org?format=json');
    const { ip } = await ipRes.json();

    // Step 2: Get location from IP (done in browser, not Azure)
    let country = 'Unknown', city = 'Unknown', countryCode = '??';
    try {
      const geoRes = await fetch(`https://ipapi.co/${ip}/json/`);
      const geo = await geoRes.json();
      country = geo.country_name || 'Unknown';
      city = geo.city || 'Unknown';
      countryCode = geo.country_code || '??';
    } catch(e) {}

    // Step 3: Send everything to Azure Function
    const res = await fetch(
      `/api/counter?ip=${ip}&country=${encodeURIComponent(country)}&city=${encodeURIComponent(city)}&cc=${countryCode}`
    );
    const data = await res.json();
    document.getElementById('counter').textContent = data.count;

  } catch(e) {
    document.getElementById('counter').textContent = '—';
  }
}
updateCounter();