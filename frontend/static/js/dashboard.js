/**
 * Plotly Analytics Dashboard Module
 * Renders and updates interactive charts for the Object Counting System.
 */

const darkLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: {
    color: '#9ca3af',
    family: 'ui-sans-serif, system-ui, sans-serif'
  },
  margin: { t: 20, b: 40, l: 50, r: 20 },
  autosize: true
};

async function loadAnalyticsData() {
  try {
    const res = await fetch('/api/analytics/plotly-data');
    if (!res.ok) throw new Error("Failed to fetch analytics data");
    const data = await res.json();

    renderDonutChart(data.donut);
    renderBarChart(data.bar);
    renderTimelineChart(data.time_series);
  } catch (err) {
    console.error("Error loading analytics:", err);
  }
}

function renderDonutChart(donutData) {
  const layout = {
    ...darkLayout,
    showlegend: true,
    legend: {
      orientation: 'h',
      y: -0.2,
      font: { size: 11 }
    }
  };

  const chartData = [{
    values: donutData.values,
    labels: donutData.labels,
    type: 'pie',
    hole: 0.55,
    marker: donutData.marker,
    textinfo: 'label+percent',
    textposition: 'outside',
    automargin: true
  }];

  Plotly.react('chart-donut', chartData, layout, { responsive: true, displayModeBar: false });
}

function renderBarChart(barData) {
  const layout = {
    ...darkLayout,
    barmode: 'group',
    xaxis: {
      gridcolor: '#1f2937',
      zerolinecolor: '#374151'
    },
    yaxis: {
      gridcolor: '#1f2937',
      zerolinecolor: '#374151'
    },
    legend: {
      orientation: 'h',
      y: -0.25,
      font: { size: 11 }
    }
  };

  Plotly.react('chart-bar', barData, layout, { responsive: true, displayModeBar: false });
}

function renderTimelineChart(timeSeriesData) {
  const times = timeSeriesData.map(d => d.time);
  const counts = timeSeriesData.map(d => d.count);

  const trace = {
    x: times.length > 0 ? times : ['12:00', '12:05', '12:10'],
    y: counts.length > 0 ? counts : [0, 0, 0],
    type: 'scatter',
    mode: 'lines+markers',
    line: { color: '#6366f1', width: 3, shape: 'spline' },
    marker: { color: '#00e5ff', size: 6 },
    fill: 'tozeroy',
    fillcolor: 'rgba(99, 102, 241, 0.15)'
  };

  const layout = {
    ...darkLayout,
    xaxis: {
      title: 'Time (UTC)',
      gridcolor: '#1f2937',
      zerolinecolor: '#374151'
    },
    yaxis: {
      title: 'Crossing Count',
      gridcolor: '#1f2937',
      zerolinecolor: '#374151'
    }
  };

  Plotly.react('chart-timeline', [trace], layout, { responsive: true, displayModeBar: false });
}

async function clearHistory() {
  if (!confirm("Are you sure you want to clear historical counting data?")) return;
  try {
    const res = await fetch('/api/analytics/clear', { method: 'POST' });
    if (res.ok) {
      alert("Historical records cleared.");
      loadAnalyticsData();
    }
  } catch (err) {
    console.error("Error clearing history:", err);
  }
}
