document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('scan-form');
  const results = document.getElementById('results');
  const reportBox = document.getElementById('report');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const target = document.getElementById('target').value.trim();
    if (!target) return;

    const response = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target })
    });

    const data = await response.json();
    if (!response.ok) {
      reportBox.innerHTML = `<p>Error: ${data.detail || 'Unknown error'}</p>`;
      results.classList.remove('hidden');
      return;
    }

    const findings = data.prioritized_findings || [];
    reportBox.innerHTML = `
      <p><strong>Target:</strong> ${data.target}</p>
      <p><strong>Status:</strong> ${data.status}</p>
      <p><strong>Total findings:</strong> ${data.summary.total_findings || 0}</p>
      <ul>
        ${findings.map(f => `<li><strong>${f.title}</strong> (${f.severity})</li>`).join('') || '<li>No findings.</li>'}
      </ul>
      <div>${data.report_html || ''}</div>
    `;
    results.classList.remove('hidden');
  });
});
