async function fetchRecords() {
  const res = await fetch('/api/records');
  return res.ok ? res.json() : [];
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString();
}

function buildTable(records) {
  const tbody = document.querySelector('#historyTable tbody');
  tbody.innerHTML = '';
  records.slice().reverse().forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${formatDate(r.created_at)}</td>
                    <td>${r.name ? r.name : '—'}</td>
                    <td>${r.height_cm}</td>
                    <td>${r.weight_kg}</td>
                    <td>${r.water_l}</td>`;
    tbody.appendChild(tr);
  });
}

function calcAvgWater(records) {
  if (!records.length) return null;
  const sum = records.reduce((s,r) => s + Number(r.water_l), 0);
  return (sum / records.length).toFixed(2);
}

let waterChart, weightChart;
let imcChart;

function renderCharts(records) {
  // Group records by user name (use '—' for unnamed)
  const byName = {};
  records.forEach(r => {
    const name = r.name && r.name.trim() ? r.name.trim() : '—';
    if (!byName[name]) byName[name] = [];
    byName[name].push(r);
  });

  // Build a unified sorted set of labels (dates) across all records
  const allDates = Array.from(new Set(records.map(r => (new Date(r.created_at)).toISOString()))).sort();
  const labels = allDates.map(d => (new Date(d)).toLocaleDateString());

  function makeDataset(name, color, key, type='line'){
    // Only place values on the dates where the user has records; leave other indices null.
    const userRecs = (byName[name] || []).map(rr => ({ iso: new Date(rr.created_at).toISOString(), val: rr[key] == null ? null : Number(rr[key]) }))
      .sort((a,b) => a.iso.localeCompare(b.iso));
    const data = allDates.map(d => null);
    const pointRadius = allDates.map(d => 0);
    userRecs.forEach(r => {
      const idx = allDates.indexOf(r.iso);
      if (idx !== -1){
        data[idx] = r.val;
        pointRadius[idx] = 6; // highlight actual record
      }
    });
    // spanGaps:true will connect consecutive non-null points for this user
    return { label: name, data, borderColor: color, backgroundColor: color, fill: false, tension: 0.2, pointRadius, pointBorderWidth: 2, spanGaps: true };
  }

  // color palette
  const palette = ['#2b8cff','#4fc3f7','#ff8c42','#8e44ad','#2ecc71','#f39c12','#e74c3c','#34495e'];

  const waterDatasets = [];
  const weightDatasets = [];
  const imcDatasets = [];
  let i = 0;
  Object.keys(byName).forEach(name => {
    const color = palette[i % palette.length];
    waterDatasets.push(Object.assign({ type: 'bar' }, makeDataset(name, color, 'water_l')));
    weightDatasets.push(makeDataset(name, color, 'weight_kg'));
    imcDatasets.push(makeDataset(name, color, 'imc'));
    i++;
  });

  const wCtx = document.getElementById('waterChart').getContext('2d');
  const pCtx = document.getElementById('weightChart').getContext('2d');
  const iCtx = document.getElementById('imcChart').getContext('2d');

  if (waterChart) waterChart.destroy();
  if (weightChart) weightChart.destroy();
  if (imcChart) imcChart.destroy();

  waterChart = new Chart(wCtx, { type: 'bar', data: { labels, datasets: waterDatasets }, options: { responsive: true } });
  weightChart = new Chart(pCtx, { type: 'line', data: { labels, datasets: weightDatasets }, options: { responsive: true } });

  // IMC chart with bands
  imcChart = new Chart(iCtx, {
    type: 'line',
    data: { labels, datasets: imcDatasets },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true, suggestedMax: 40 } },
      plugins: { legend: { display: true } }
    },
    plugins: [{
      id: 'imcBands',
      beforeDraw: (chart) => {
        const ctx = chart.ctx;
        const yScale = chart.scales.y;
        const xLeft = chart.chartArea.left;
        const xRight = chart.chartArea.right;
        function drawBand(yValueTop, yValueBottom, color) {
          const yTop = yScale.getPixelForValue(yValueTop);
          const yBottom = yScale.getPixelForValue(yValueBottom);
          ctx.fillStyle = color;
          ctx.fillRect(xLeft, yTop, xRight - xLeft, yBottom - yTop);
        }
        drawBand(0, 18.5, 'rgba(144,202,249,0.2)');
        drawBand(18.5, 24.9, 'rgba(102,187,106,0.15)');
        drawBand(25, 29.9, 'rgba(255,183,77,0.12)');
        drawBand(30, yScale.max || 40, 'rgba(229,115,115,0.12)');
      }
    }]
  });
}

async function refreshAll() {
  const records = await fetchRecords();
  buildTable(records);
  renderCharts(records);
  const avg = calcAvgWater(records);
  document.getElementById('avgWater').textContent = avg ? `${avg} L` : '—';
  const last = records.length ? records[records.length - 1].weight_kg : '—';
  document.getElementById('lastWeight').textContent = last;
  const lastImc = records.length ? records[records.length - 1].imc : null;
  document.getElementById('lastImc').textContent = lastImc ? lastImc.toFixed(2) : '—';
  document.getElementById('imcClass').textContent = classifyImc(lastImc);
}

document.addEventListener('DOMContentLoaded', () => {
  refreshAll();

  const clearBtn = document.getElementById('clearBtn');
  if (clearBtn) clearBtn.addEventListener('click', () => { document.getElementById('recordForm').reset(); });

  // Export button (fetch)
  const exportBtn = document.getElementById('exportBtn');
  if (exportBtn) exportBtn.addEventListener('click', exportCsvFetch);

  // Trim name and other fields before submit; prevent name with only spaces
  const form = document.getElementById('recordForm');
  if (form) {
    form.addEventListener('submit', (e) => {
      const nameEl = form.querySelector('input[name="name"]');
      if (nameEl) {
        const trimmed = nameEl.value.trim();
        nameEl.value = trimmed; // clear only-spaces
      }
      // also trim numeric inputs to be safe
      ['height_cm','weight_kg','water_l'].forEach(n => {
        const el = form.querySelector(`input[name="${n}"]`);
        if (el && typeof el.value === 'string') el.value = el.value.trim();
      });
    });
  }
});

function classifyImc(imc){
  if (imc === null || imc === undefined) return '—';
  imc = Number(imc);
  if (isNaN(imc)) return '—';
  if (imc < 18.5) return 'Magro';
  if (imc >= 18.5 && imc <= 24.9) return 'Normal';
  if (imc >= 25 && imc <= 29.9) return 'Sobrepeso';
  if (imc >= 30) return 'Obesidade';
  return '—';
}

// Export CSV via fetch and trigger download
async function exportCsvFetch(){
  try{
    const resp = await fetch('/export');
    if(!resp.ok) throw new Error('Não foi possível baixar');
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'records.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }catch(e){
    alert('Erro ao exportar CSV: '+e.message);
  }
}
