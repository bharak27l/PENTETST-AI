import { useCallback, useEffect, useState } from 'react';

const API = '/api';

export default function Dashboard() {
  const [token, setToken] = useState(localStorage.getItem('pentest_token') || '');
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [history, setHistory] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [jobRuns, setJobRuns] = useState({});
  const [report, setReport] = useState(null);
  const [target, setTarget] = useState('');
  const [jobTarget, setJobTarget] = useState('');
  const [jobInterval, setJobInterval] = useState(3600);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user' });
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const request = useCallback((path, options = {}) => fetch(`${API}${path}`, {
    ...options,
    headers: { ...(options.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  }), [token]);

  const signOut = useCallback(() => {
    localStorage.removeItem('pentest_token');
    setToken(''); setUser(null); setHistory([]); setJobs([]); setJobRuns({}); setReport(null); setUsers([]);
  }, []);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const [scanResponse, jobResponse, meResponse] = await Promise.all([
        request('/scans'), request('/jobs'), request('/auth/me'),
      ]);
      if ([scanResponse, jobResponse, meResponse].some(response => response.status === 401)) {
        signOut(); return;
      }
      if (!scanResponse.ok || !jobResponse.ok || !meResponse.ok) throw new Error('Could not refresh dashboard data.');
      setHistory((await scanResponse.json()).items || []);
      setJobs((await jobResponse.json()).items || []);
      setUser(await meResponse.json());
    } catch (err) { setError(err.message); }
  }, [request, signOut, token]);

  const loadUsers = useCallback(async () => {
    if (!token) return;
    try {
      const response = await request('/admin/users');
      if (response.status === 403) { setUsers([]); return; }
      if (!response.ok) throw new Error('Could not load users.');
      setUsers((await response.json()).items || []);
    } catch (err) { setError(err.message); }
  }, [request, token]);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { if (user?.role === 'admin') loadUsers(); }, [user, loadUsers]);

  async function signIn(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const response = await fetch(`${API}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Sign in failed.');
      localStorage.setItem('pentest_token', data.access_token);
      setToken(data.access_token); setUser(data.user); setPassword('');
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function submitScan(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      const response = await request('/scan', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Scan request failed.');
      setReport(data); setTarget(''); setNotice('Safe assessment completed.'); await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function createJob(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      const response = await request('/jobs', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: jobTarget, interval_seconds: Number(jobInterval), enabled: true }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Job creation failed.');
      setJobTarget(''); setNotice('Scheduled job created.'); await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function updateJob(job, patch) {
    setError('');
    try {
      const response = await request(`/jobs/${encodeURIComponent(job.id)}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Job update failed.');
      await refresh();
    } catch (err) { setError(err.message); }
  }

  async function deleteJob(job) {
    if (!window.confirm(`Delete scheduled job for ${job.target}?`)) return;
    const response = await request(`/jobs/${encodeURIComponent(job.id)}`, { method: 'DELETE' });
    if (!response.ok) { setError('Could not delete job.'); return; }
    setJobs(current => current.filter(item => item.id !== job.id));
  }

  async function showRuns(jobId) {
    setError('');
    try {
      const response = await request(`/jobs/${encodeURIComponent(jobId)}/runs`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not load job history.');
      setJobRuns(current => ({ ...current, [jobId]: data.items || [] }));
    } catch (err) { setError(err.message); }
  }

  async function createUser(event) {
    event.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      const response = await request('/admin/users', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newUser),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'User creation failed.');
      setNewUser({ username: '', password: '', role: 'user' });
      setNotice(`Created account ${data.user.username}.`); await loadUsers();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function openScan(id) {
    setError('');
    const response = await request(`/scans/${encodeURIComponent(id)}`);
    const data = await response.json();
    if (!response.ok) { setError(data.detail || 'Could not load report.'); return; }
    setReport(data);
  }

  async function download(format) {
    if (!report?.id) return;
    const response = await request(`/scans/${encodeURIComponent(report.id)}/export/${format}`);
    if (!response.ok) { setError('Could not export report.'); return; }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = `pentest-report.${format}`; anchor.click();
    URL.revokeObjectURL(url);
  }

  if (!token) return <main className="layout auth-layout"><header className="topbar"><div><div className="eyebrow">AUTHORIZED SECURITY TESTING</div><h1>PENTETST-AI</h1></div><span className="safe-badge">Safe checks only</span></header><section className="panel auth-panel"><h2>Sign in</h2><p>Use an account provisioned by your administrator.</p><form onSubmit={signIn} className="auth-form"><label>Username<input autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required /></label><label>Password<input type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required /></label><button disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button></form>{error && <div role="alert" className="error">{error}</div>}</section></main>;

  const findings = report?.prioritized_findings || report?.findings || [];
  return <main className="layout">
    <header className="topbar"><div><div className="eyebrow">AUTHORIZED SECURITY TESTING</div><h1>PENTETST-AI</h1></div><div className="top-actions"><span className="safe-badge">{user?.username} · {user?.role}</span><button className="secondary" onClick={signOut}>Sign out</button></div></header>
    {error && <div role="alert" className="error">{error}</div>}{notice && <div role="status" className="notice">{notice}</div>}
    <section className="panel hero"><h2>Assessment dashboard</h2><p>Safe metadata and security-header checks for authorized targets.</p><form onSubmit={submitScan} className="scan-form"><label htmlFor="target">Authorized target URL</label><div className="input-row"><input id="target" type="url" required value={target} onChange={event => setTarget(event.target.value)} placeholder="https://example.com" /><button disabled={busy}>{busy ? 'Working…' : 'Run safe checks'}</button></div><small>Only test systems you own or have explicit permission to assess.</small></form></section>
    {report && <section className="panel"><div className="section-heading"><div><div className="eyebrow">REPORT</div><h2>{report.target}</h2></div><div className="exports">{['pdf', 'docx', 'json'].map(format => <button key={format} onClick={() => download(format)}>{format.toUpperCase()}</button>)}</div></div><div className="stats"><div><strong>{report.summary?.total_findings ?? findings.length}</strong><span>Findings</span></div><div><strong>{report.summary?.high ?? 0}</strong><span>High</span></div><div><strong>{report.summary?.medium ?? 0}</strong><span>Medium</span></div><div><strong>{report.summary?.low ?? 0}</strong><span>Low</span></div></div>{findings.map((item, index) => <article className="finding" key={`${item.id || 'finding'}-${index}`}><div className="finding-head"><h3>{item.title}</h3><span className={`severity ${item.severity}`}>{item.severity}</span></div><p>{item.recommendation}</p></article>)}</section>}
    <section className="panel"><div className="section-heading"><div><div className="eyebrow">SCHEDULED JOBS</div><h2>Recurring scans</h2></div></div><form onSubmit={createJob} className="schedule-form"><div className="input-row schedule-grid"><input type="url" required value={jobTarget} onChange={event => setJobTarget(event.target.value)} placeholder="https://example.com" /><label className="interval-label">Interval (seconds)<input type="number" min="60" max="86400" value={jobInterval} onChange={event => setJobInterval(Number(event.target.value))} /></label><button disabled={busy}>Create job</button></div></form>{jobs.length ? jobs.map(job => <article className="job-card" key={job.id}><div className="job-summary"><div><strong>{job.target}</strong><small>Every {job.interval_seconds}s · {job.status}{job.last_run_at ? ` · Last run ${new Date(job.last_run_at).toLocaleString()}` : ''}</small></div><div className="job-actions"><button className="secondary" onClick={() => updateJob(job, { enabled: !job.enabled })}>{job.enabled ? 'Pause' : 'Resume'}</button><button className="secondary" onClick={() => showRuns(job.id)}>Run history</button><button className="danger" onClick={() => deleteJob(job)}>Delete</button></div></div>{jobRuns[job.id] && <div className="run-history">{jobRuns[job.id].length ? jobRuns[job.id].map(run => <p key={run.id}><strong>{run.status}</strong> · {new Date(run.started_at).toLocaleString()}</p>) : <p>No executions recorded.</p>}</div>}</article>) : <p className="muted">No scheduled jobs yet. Scheduling must be enabled by the operator.</p>}</section>
    <section className="panel"><div className="section-heading"><div><div className="eyebrow">PERSISTED RESULTS</div><h2>Scan history</h2></div><button className="secondary" onClick={refresh}>Refresh</button></div>{history.length ? history.map(item => <button className="history-row" key={item.id} onClick={() => openScan(item.id)}><span><strong>{item.target}</strong><small>{new Date(item.created_at).toLocaleString()}</small></span><span>{item.summary?.total_findings ?? 0} findings</span></button>) : <p className="muted">No saved scans yet.</p>}</section>
    {user?.role === 'admin' && <section className="panel"><div className="eyebrow">ADMINISTRATION</div><h2>Users</h2><form onSubmit={createUser} className="auth-form"><label>Username<input minLength="3" value={newUser.username} onChange={event => setNewUser({ ...newUser, username: event.target.value })} required /></label><label>Temporary password<input type="password" minLength="12" value={newUser.password} onChange={event => setNewUser({ ...newUser, password: event.target.value })} required /></label><label>Role<select value={newUser.role} onChange={event => setNewUser({ ...newUser, role: event.target.value })}><option value="user">User</option><option value="admin">Admin</option></select></label><button disabled={busy}>Create account</button></form><div className="user-list">{users.map(item => <p key={item.id}>{item.username} <span className="muted">· {item.role}</span></p>)}</div></section>}
    <footer>Nuclei/ZAP adapters are not implemented. No external scanner is launched.</footer>
  </main>;
}
