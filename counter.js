async function updateCounter() {
  const res = await fetch('/api/counter');
  const data = await res.json();
  document.getElementById('counter').textContent = data.count;
}
updateCounter();