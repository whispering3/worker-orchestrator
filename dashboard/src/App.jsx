import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  PlusCircle, 
  Trash2, 
  RefreshCw, 
  Database, 
  AlertOctagon,
  CheckCircle2,
  Play
} from 'lucide-react';

const API_BASE = "http://localhost:8000";

const App = () => {
  const [jobs, setJobs] = useState([]);
  const [dlq, setDlq] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ queue: 'default', payload: '', priority: 0 });
  const [stats, setStats] = useState({ total: 0, pending: 0, running: 0, done: 0, dead: 0 });

  const fetchData = async () => {
    try {
      // Em uma aplicação real, você teria um endpoint de stats
      // Aqui vamos buscar da DLQ e talvez de uma lista de jobs recentes
      const dlqRes = await fetch(`${API_BASE}/admin/dlq?queue=${form.queue}`);
      const dlqData = await dlqRes.json();
      setDlq(dlqData);

      // Atualiza contadores simples
      setStats(prev => ({ ...prev, dead: dlqData.length }));
    } catch (err) {
      console.error("Erro ao buscar dados:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Auto refresh
    return () => clearInterval(interval);
  }, [form.queue]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          queue: form.queue,
          payload: JSON.parse(form.payload || '{}'),
          priority: parseInt(form.priority)
        })
      });
      if (res.ok) {
        setForm({ ...form, payload: '' });
        alert("Job enviado com sucesso!");
        fetchData();
      }
    } catch (err) {
      alert("Erro ao enviar job: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReprocess = async (id) => {
    try {
      await fetch(`${API_BASE}/admin/dlq/${id}/reprocess`, { method: 'POST' });
      fetchData();
    } catch (err) {
      alert("Erro ao reprocessar");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Tem certeza que deseja deletar este job?")) return;
    try {
      await fetch(`${API_BASE}/admin/dlq/${id}`, { method: 'DELETE' });
      fetchData();
    } catch (err) {
      alert("Erro ao deletar");
    }
  };

  return (
    <div className="container">
      <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="gradient-text" style={{ fontSize: '2.5rem' }}>Worker Orchestrator</h1>
          <p style={{ color: 'var(--text-dim)', marginTop: '0.5rem' }}>PostgreSQL-based Job Queue Management</p>
        </div>
        <div className="card" style={{ padding: '0.5rem 1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <Database size={18} color="var(--primary)" />
          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>PG.V16.STABLE</span>
        </div>
      </header>

      {/* Stats Section */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        <StatCard icon={<Activity />} title="Em Execução" value={stats.running} color="var(--primary)" />
        <StatCard icon={<CheckCircle2 />} title="Concluídos" value={stats.done} color="var(--success)" />
        <StatCard icon={<AlertOctagon />} title="Dead Letter Queue" value={stats.dead} color="var(--danger)" />
        <StatCard icon={<PlusCircle />} title="Pendentes" value={stats.pending} color="var(--warning)" />
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '2rem' }}>
        {/* DLQ Manager */}
        <section className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2>Dead Letter Queue</h2>
            <button className="btn btn-outline" onClick={fetchData}><RefreshCw size={16} /></button>
          </div>
          
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Payload</th>
                  <th>Último Erro</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {dlq.length === 0 ? (
                  <tr><td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>Nenhum job na DLQ</td></tr>
                ) : dlq.map(job => (
                  <tr key={job.id}>
                    <td style={{ fontSize: '0.8rem', opacity: 0.7 }}>{job.id.slice(0, 8)}...</td>
                    <td style={{ fontSize: '0.8rem' }}><code>{JSON.stringify(job.payload)}</code></td>
                    <td style={{ color: 'var(--danger)', fontSize: '0.8rem' }}>{job.last_error}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => handleReprocess(job.id)}>
                          <Play size={14} color="var(--success)" />
                        </button>
                        <button className="btn btn-outline" style={{ padding: '4px 8px' }} onClick={() => handleDelete(job.id)}>
                          <Trash2 size={14} color="var(--danger)" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* New Job Form */}
        <section className="card">
          <h2 style={{ marginBottom: '1.5rem' }}>Novo Job</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '1.2rem' }}>
              <label>Fila (Queue)</label>
              <input 
                value={form.queue} 
                onChange={e => setForm({...form, queue: e.target.value})}
                placeholder="Ex: default"
              />
            </div>
            <div style={{ marginBottom: '1.2rem' }}>
              <label>Prioridade (Maior = Mais Urgente)</label>
              <input 
                type="number"
                value={form.priority} 
                onChange={e => setForm({...form, priority: e.target.value})}
              />
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <label>Payload (JSON)</label>
              <textarea 
                rows="5"
                value={form.payload} 
                onChange={e => setForm({...form, payload: e.target.value})}
                placeholder='{"action": "send_email", "to": "user@ex.com"}'
                style={{ resize: 'none' }}
              />
            </div>
            <button className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? "Enviando..." : "Submeter Job"}
            </button>
          </form>
        </section>
      </div>
    </div>
  );
};

const StatCard = ({ icon, title, value, color }) => (
  <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.2rem' }}>
    <div style={{ 
      background: `${color}20`, 
      color: color, 
      padding: '1rem', 
      borderRadius: '15px' 
    }}>
      {React.cloneElement(icon, { size: 24 })}
    </div>
    <div>
      <p style={{ color: 'var(--text-dim)', fontSize: '0.875rem' }}>{title}</p>
      <h3 style={{ fontSize: '1.5rem', marginTop: '0.2rem' }}>{value}</h3>
    </div>
  </div>
);

export default App;
