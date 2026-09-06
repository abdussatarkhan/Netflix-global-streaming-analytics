// dashboard/dashboard.js
// Netflix Performance Analytics Interactive Visualizations Engine

async function loadAndInitDashboard() {
  try {
    const res = await fetch('data.json');
    const data = await res.json();
    initDashboard(data);
  } catch (err) {
    console.error('Failed to load data.json', err);
  }
}

if (typeof window !== 'undefined') {
  window.loadAndInitDashboard = loadAndInitDashboard;
}
