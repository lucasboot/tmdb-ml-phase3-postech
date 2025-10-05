let chartTop, chartPopularity, chartVoteAverage;

async function fetchSummary(){
  const r = await fetch('/api/summary');
  const j = await r.json();
  return j.top || [];
}

async function fetchPredictions(){
  const r = await fetch('/api/predictions');
  const j = await r.json();
  return j.predictions || [];
}

function renderTopTable(rows){
  const html = rows.map(r => `<tr><td>${r.title}</td><td>${r.popularity.toFixed(2)}</td><td>${r.vote_count}</td><td>${r.vote_average?.toFixed(1) ?? '-'}</td></tr>`).join('');
  document.getElementById('tblTop').innerHTML = html;
}

function renderTopChart(rows){
  const labels = rows.map(r => r.title);
  const data = rows.map(r => r.popularity);
  if (chartTop) chartTop.destroy();
  chartTop = new Chart(document.getElementById('chartTop'), {
    type: 'bar',
    data: { 
      labels, 
      datasets: [{ 
        label: 'Popularity', 
        data,
        backgroundColor: 'rgba(54, 162, 235, 0.6)'
      }] 
    },
    options: { 
      responsive: true, 
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } }
    }
  });
}

function renderPredictionsTable(preds){
  const html = preds.slice(0, 10).map(p => `
    <tr>
      <td>${p.title}</td>
      <td>${p.release_date || '-'}</td>
      <td>${p.predicted_popularity.toFixed(2)}</td>
      <td>${p.actual_popularity.toFixed(2)}</td>
      <td>${p.predicted_vote_average.toFixed(2)}</td>
      <td>${p.actual_vote_average.toFixed(2)}</td>
    </tr>
  `).join('');
  document.getElementById('tblPredictions').innerHTML = html;
}

function renderMetrics(preds){
  if (preds.length === 0) return;
  const p = preds[0];
  const html = `
    <tr><td>MAE Popularidade</td><td>${p.mae_popularity?.toFixed(2) || 'N/A'}</td></tr>
    <tr><td>MAE Nota Média</td><td>${p.mae_vote_average?.toFixed(2) || 'N/A'}</td></tr>
  `;
  document.getElementById('tblMetrics').innerHTML = html;
}

function renderPopularityChart(preds){
  const top15 = preds.slice(0, 15);
  const labels = top15.map(p => p.title.substring(0, 30));
  const predicted = top15.map(p => p.predicted_popularity);
  const actual = top15.map(p => p.actual_popularity);
  
  if (chartPopularity) chartPopularity.destroy();
  chartPopularity = new Chart(document.getElementById('chartPopularity'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Previsto',
          data: predicted,
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          fill: false
        },
        {
          label: 'Real',
          data: actual,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true } }
    }
  });
}

function renderVoteAverageChart(preds){
  const top15 = preds.slice(0, 15);
  const labels = top15.map(p => p.title.substring(0, 30));
  const predicted = top15.map(p => p.predicted_vote_average);
  const actual = top15.map(p => p.actual_vote_average);
  
  if (chartVoteAverage) chartVoteAverage.destroy();
  chartVoteAverage = new Chart(document.getElementById('chartVoteAverage'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Previsto',
          data: predicted,
          borderColor: 'rgba(153, 102, 255, 1)',
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          fill: false
        },
        {
          label: 'Real',
          data: actual,
          borderColor: 'rgba(255, 206, 86, 1)',
          backgroundColor: 'rgba(255, 206, 86, 0.2)',
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { 
        y: { 
          beginAtZero: false,
          min: 0,
          max: 10
        } 
      }
    }
  });
}

async function refresh(){
  const [top, preds] = await Promise.all([fetchSummary(), fetchPredictions()]);
  
  renderTopTable(top);
  renderTopChart(top);
  
  if (preds.length > 0) {
    renderPredictionsTable(preds);
    renderPopularityChart(preds);
    renderVoteAverageChart(preds);
    renderMetrics(preds);
  }
}

window.addEventListener('load', async () => {
  await refresh();
  const pollMs = parseInt(document.querySelector('small').innerText.match(/\d+/)[0]) * 1000;
  setInterval(refresh, pollMs);
});

