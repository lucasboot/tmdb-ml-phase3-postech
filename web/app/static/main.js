let chartFeatureImportance, chartRealVsPredicted, chartConfusionMatrix, chartROC, chartPCA, chartClusterProfiles;

async function fetchFeatureImportance(){
  const r = await fetch('/api/horror/regression/features');
  const j = await r.json();
  return j;
}

async function fetchRegressionPredictions(){
  const r = await fetch('/api/horror/regression/predictions');
  const j = await r.json();
  return j.predictions || [];
}

async function fetchClassification(){
  const r = await fetch('/api/horror/classification');
  const j = await r.json();
  return j;
}

async function fetchClusteringPCA(){
  const r = await fetch('/api/horror/clustering/pca');
  const j = await r.json();
  return j.clusters || [];
}

async function fetchClusteringProfiles(){
  const r = await fetch('/api/horror/clustering/profiles');
  const j = await r.json();
  return j.profiles || [];
}

function renderFeatureImportanceChart(data){
  if (!data.features || data.features.length === 0) return;
  
  const top10 = data.features.slice(0, 10);
  const labels = top10.map(f => f.name);
  const values = top10.map(f => f.importance);
  
  if (chartFeatureImportance) chartFeatureImportance.destroy();
  chartFeatureImportance = new Chart(document.getElementById('chartFeatureImportance'), {
    type: 'bar',
    data: { 
      labels, 
      datasets: [{ 
        label: 'Importância', 
        data: values,
        backgroundColor: 'rgba(153, 102, 255, 0.7)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 1
      }] 
    },
    options: { 
      indexAxis: 'y',
      responsive: true, 
      maintainAspectRatio: false,
      scales: { 
        x: { 
          beginAtZero: true,
          title: { display: true, text: 'Importância Normalizada' }
        }
      }
    }
  });
  
  const metricsHtml = `
    <tr><td>MAE (Mean Absolute Error)</td><td>${data.metrics.mae?.toFixed(2) || 'N/A'}</td></tr>
    <tr><td>R² Score</td><td>${data.metrics.r2_score?.toFixed(3) || 'N/A'}</td></tr>
  `;
  document.getElementById('tblRegressionMetrics').innerHTML = metricsHtml;
}

function renderRealVsPredictedChart(predictions){
  if (!predictions || predictions.length === 0) return;
  
  const actualValues = predictions.map(p => p.actual);
  const predictedValues = predictions.map(p => p.predicted);
  
  const maxActual = Math.max(...actualValues);
  const maxPredicted = Math.max(...predictedValues);
  const maxValue = Math.max(maxActual, maxPredicted);
  
  const p90Actual = actualValues.sort((a, b) => a - b)[Math.floor(actualValues.length * 0.9)];
  const p90Predicted = predictedValues.sort((a, b) => a - b)[Math.floor(predictedValues.length * 0.9)];
  const p90Max = Math.max(p90Actual, p90Predicted);
  
  const axisMax = maxValue > p90Max * 2 ? Math.ceil(p90Max * 1.4) : Math.ceil(maxValue * 1.2);
  
  if (chartRealVsPredicted) chartRealVsPredicted.destroy();
  chartRealVsPredicted = new Chart(document.getElementById('chartRealVsPredicted'), {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'Diagonal de Referência',
          data: [{ x: 0, y: 0 }, { x: axisMax, y: axisMax }],
          type: 'line',
          borderColor: 'rgba(128, 128, 128, 0.5)',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
          borderWidth: 2
        },
        {
          label: 'Filmes de Terror',
          data: predictions.map(p => ({ x: p.actual, y: p.predicted })),
          backgroundColor: 'rgba(255, 99, 132, 0.6)',
          borderColor: 'rgba(255, 99, 132, 1)',
          pointRadius: 5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: 'Popularidade Real' },
          beginAtZero: true,
          max: axisMax
        },
        y: {
          title: { display: true, text: 'Popularidade Prevista' },
          beginAtZero: true,
          max: axisMax
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              if (context.dataset.label === 'Diagonal de Referência') return null;
              const p = predictions[context.dataIndex];
              return `${p.title}: (${p.actual.toFixed(1)}, ${p.predicted.toFixed(1)})`;
            }
          }
        }
      }
    }
  });
}

function renderConfusionMatrixChart(classification){
  if (!classification.confusion_matrix || classification.confusion_matrix.length === 0) return;
  
  const cm = classification.confusion_matrix;
  
  if (chartConfusionMatrix) chartConfusionMatrix.destroy();
  chartConfusionMatrix = new Chart(document.getElementById('chartConfusionMatrix'), {
    type: 'bar',
    data: {
      labels: ['TN (Baixa→Baixa)', 'FP (Baixa→Alta)', 'FN (Alta→Baixa)', 'TP (Alta→Alta)'],
      datasets: [{
        label: 'Quantidade',
        data: [cm[0][0], cm[0][1], cm[1][0], cm[1][1]],
        backgroundColor: [
          'rgba(75, 192, 192, 0.7)',
          'rgba(255, 159, 64, 0.7)',
          'rgba(255, 99, 132, 0.7)',
          'rgba(54, 162, 235, 0.7)'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

function renderROCChart(classification){
  if (!classification.roc_curve || !classification.roc_curve.fpr) return;
  
  const fpr = classification.roc_curve.fpr;
  const tpr = classification.roc_curve.tpr;
  
  const rocData = fpr.map((f, i) => ({ x: f, y: tpr[i] }));
  const diagonalData = [{ x: 0, y: 0 }, { x: 1, y: 1 }];
  
  if (chartROC) chartROC.destroy();
  chartROC = new Chart(document.getElementById('chartROC'), {
    type: 'line',
    data: {
      datasets: [
        {
          label: `ROC Curve (AUC = ${classification.metrics.auc?.toFixed(3) || 'N/A'})`,
          data: rocData,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          fill: true,
          pointRadius: 0,
          borderWidth: 2,
          tension: 0.1
        },
        {
          label: 'Random Classifier',
          data: diagonalData,
          borderColor: 'rgba(255, 99, 132, 1)',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: 'linear',
          title: { display: true, text: 'Taxa de Falsos Positivos' },
          min: 0,
          max: 1
        },
        y: {
          type: 'linear',
          title: { display: true, text: 'Taxa de Verdadeiros Positivos' },
          min: 0,
          max: 1
        }
      },
      plugins: {
        legend: {
          display: true
        }
      }
    }
  });
  
  const metricsHtml = `
    <tr><td>AUC (Area Under Curve)</td><td>${classification.metrics.auc?.toFixed(3) || 'N/A'}</td></tr>
    <tr><td>Accuracy</td><td>${classification.metrics.accuracy?.toFixed(3) || 'N/A'}</td></tr>
  `;
  document.getElementById('tblClassificationMetrics').innerHTML = metricsHtml;
}

function renderPCAChart(clusters){
  if (!clusters || clusters.length === 0) return;
  
  const uniqueClusters = [...new Set(clusters.map(c => c.cluster_id))];
  const colors = [
    'rgba(255, 99, 132, 0.7)',
    'rgba(54, 162, 235, 0.7)',
    'rgba(75, 192, 192, 0.7)',
    'rgba(153, 102, 255, 0.7)',
    'rgba(255, 159, 64, 0.7)',
    'rgba(255, 206, 86, 0.7)'
  ];
  
  const datasets = uniqueClusters.map(clusterId => {
    const clusterData = clusters.filter(c => c.cluster_id === clusterId);
    return {
      label: `Cluster ${clusterId}`,
      data: clusterData.map(c => ({ x: c.pca_x, y: c.pca_y })),
      backgroundColor: colors[clusterId % colors.length],
      borderColor: colors[clusterId % colors.length].replace('0.7', '1'),
      pointRadius: 6
    };
  });
  
  if (chartPCA) chartPCA.destroy();
  chartPCA = new Chart(document.getElementById('chartPCA'), {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { title: { display: true, text: 'Componente Principal 1' } },
        y: { title: { display: true, text: 'Componente Principal 2' } }
      }
    }
  });
}

function renderClusterProfilesChart(profiles){
  if (!profiles || profiles.length === 0) return;
  
  const labels = profiles.map(p => `Cluster ${p.cluster_id} (${p.movie_count} filmes)`);
  
  if (chartClusterProfiles) chartClusterProfiles.destroy();
  chartClusterProfiles = new Chart(document.getElementById('chartClusterProfiles'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Popularidade Média',
          data: profiles.map(p => p.avg_popularity),
          backgroundColor: 'rgba(255, 99, 132, 0.7)',
          yAxisID: 'y'
        },
        {
          label: 'Avaliação Média',
          data: profiles.map(p => p.avg_vote_average),
          backgroundColor: 'rgba(54, 162, 235, 0.7)',
          yAxisID: 'y1'
        },
        {
          label: 'Duração Média (min)',
          data: profiles.map(p => p.avg_runtime),
          backgroundColor: 'rgba(75, 192, 192, 0.7)',
          yAxisID: 'y2'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          title: { display: true, text: 'Popularidade' }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          title: { display: true, text: 'Avaliação (0-10)' },
          grid: {
            drawOnChartArea: false
          },
          min: 0,
          max: 10
        },
        y2: {
          type: 'linear',
          display: false,
          position: 'right'
        }
      }
    }
  });
}

async function refresh(){
  try {
    const [features, predictions, classification, clustersPCA, profiles] = await Promise.all([
      fetchFeatureImportance(),
      fetchRegressionPredictions(),
      fetchClassification(),
      fetchClusteringPCA(),
      fetchClusteringProfiles()
    ]);
    
    console.log('Features:', features);
    console.log('Predictions:', predictions);
    console.log('Classification:', classification);
    console.log('Clusters PCA:', clustersPCA);
    console.log('Profiles:', profiles);
    
    renderFeatureImportanceChart(features);
    renderRealVsPredictedChart(predictions);
    renderConfusionMatrixChart(classification);
    renderROCChart(classification);
    renderPCAChart(clustersPCA);
    renderClusterProfilesChart(profiles);
  } catch (error) {
    console.error('Erro ao atualizar dashboard:', error);
  }
}

window.addEventListener('load', async () => {
  await refresh();
  const pollMs = parseInt(document.querySelector('small').innerText.match(/\d+/)[0]) * 1000;
  setInterval(refresh, pollMs);
});