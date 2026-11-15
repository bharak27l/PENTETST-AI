import { useCallback, useEffect, useState } from 'react';

const API = '/api';

export default function Dashboard() {
  const [target, setTarget] = useState('');
  const [history, setHistory] = useState([]);
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch(`${API}/scans`);
      if (!response.ok) throw new Error('Could not load scan history.');
      const data = await response.json();
      setHistory(data.items || []);
    } catch (err) { setError(err.message); }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setError(''); setReport(null);
    try {
      const response = await fetch(`${API}/scan`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Scan request failed.');
      setReport(data); setTarget(''); await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function openScan(id) {
    setError('');
    try {
      const response = await fetch(`${API}/scans/${encodeURIComponent(id)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not load report.');
      setReport(data);
    } catch (err) { setError(err.message); }
  }

  const findings = report?.prioritized_findings || report?.findings || [];
  return <main className="layout">
    <header className="topbar"><div><div className="eyebrow">AUTHORIZED SECURITY TESTING</div><h1>PENTETST-AI</h1></div><span className="safe-badge">Safe checks only</span></header>
    <section className="panel hero"><div><h2>Assessment dashboard</h2><p>Collect safe target metadata, review security headers, and export reports.</p></div>
      <form onSubmit={submit} className="scan-form"><label htmlFor="target">Authorized target URL</label><div className="input-row"><input id="target" type="url" required value={target} onChange={e => setTarget(e.target.value)} placeholder="https://example.com" /><button disabled={busy}>{busy ? 'Assessing…' : 'Run safe checks'}</button></div><small>Only scan systems you own or have explicit permission to assess.</small></form>
    </section>
    {error && <div role="alert" className="error">{error}</div>}
    {report && <section className="panel"><div className="section-heading"><div><div className="eyebrow">REPORT</div><h2>{report.target}</h2></div><div className="exports">{['pdf', 'docx', 'json'].map(format => <a key={format} href={`${API}/scans/${encodeURIComponent(report.id)}/export/${format}`}>{format.toUpperCase()}</a>)}</div></div><div className="stats"><div><strong>{report.summary?.total_findings ?? findings.length}</strong><span>Findings</span></div><div><strong>{report.summary?.high ?? 0}</strong><span>High</span></div><div><strong>{report.summary?.medium ?? 0}</strong><span>Medium</span></div><div><strong>{report.summary?.low ?? 0}</strong><span>Low</span></div></div><div className="findings">{findings.length ? findings.map((item, index) => <article className="finding" key={`${item.id}-${index}`}><div className="finding-head"><h3>{item.title}</h3><span className={`severity ${item.severity}`}>{item.severity}</span></div><p>{item.recommendation}</p><small>{item.category}</small></article>) : <p>No findings detected by the configured checks.</p>}</div></section>}
    <section className="panel"><div className="section-heading"><div><div className="eyebrow">PERSISTED RESULTS</div><h2>Scan history</h2></div><button className="secondary" onClick={refresh}>Refresh</button></div>{history.length ? <div className="history">{history.map(item => <button className="history-row" key={item.id} onClick={() => openScan(item.id)}><span><strong>{item.target}</strong><small>{new Date(item.created_at).toLocaleString()}</small></span><span className="history-count">{item.summary?.total_findings ?? 0} findings</span></button>)}</div> : <p className="muted">No saved scans yet.</p>}</section>
    <footer>External scanner integrations (Nuclei/ZAP) are disabled; no scanner processes are launched.</footer>
  </main>;
}
