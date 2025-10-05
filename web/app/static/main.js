let chart;
const ctx = () => document.getElementById('chartTop');
const tbl = () => document.getElementById('tblTop');

async function fetchSummary(){
  const r = await fetch('/api/summary');
  const j = await r.json();
  return j.top || [];
}

function renderTable(rows){
  const html = rows.map(r => `<tr><td>${r.title}</td><td>${r.popularity.toFixed(2)}</td><td>${r.vote_count}</td><td>${r.vote_average?.toFixed(1) ?? '-'}</td></tr>`).join('');
  tbl().innerHTML = html;
}

function renderChart(rows){
  const labels = rows.map(r => r.title);
  const data = rows.map(r => r.popularity);
  if (chart) chart.destroy();
  chart = new Chart(ctx(), {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Popularity', data }] },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

async function refresh(){
  const rows = await fetchSummary();
  renderTable(rows);
  renderChart(rows);
}

window.addEventListener('load', async () => {
  await refresh();
  const pollMs = parseInt(document.querySelector('small').innerText.match(/\d+/)[0]) * 1000;
  setInterval(refresh, pollMs);
});

