import React, { useState, useEffect, useMemo } from 'react';
import { 
  TrendingUp, Search, CheckCircle2, XCircle, 
  BarChart3, RefreshCw, Info, Download, Calendar 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import * as XLSX from 'xlsx';

const RULES = [
  { id: 0, label: "P > 50", title: "Price > 50-day SMA" },
  { id: 1, label: "P > 150", title: "Price > 150-day SMA" },
  { id: 2, label: "P > 200", title: "Price > 200-day SMA" },
  { id: 3, label: "50 > 150", title: "50-day SMA > 150-day SMA" },
  { id: 4, label: "150 > 200", title: "150-day SMA > 200-day SMA" },
  { id: 5, label: "200 Up", title: "200-day SMA Trending Up" },
  { id: 6, label: "> 30% Lo", title: "30%+ Above 52-week Low" },
  { id: 7, label: "< 25% Hi", title: "Within 25% of 52-week High" },
  { id: 8, label: "RS > 70", title: "RS Rating > 70" },
  { id: 9, label: "P > 1m", title: "Price > 1-month-ago Price" }
];

const IS_LOCAL = window.location.hostname === 'localhost';
const API_ENDPOINT = import.meta.env.VITE_API_URL || (IS_LOCAL ? 'http://localhost:5000/api' : null);

function App() {
  const [data, setData] = useState([]);
  const [viewState, setViewState] = useState({ loading: false, label: 'Idle' });
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [query, setQuery] = useState('');
  const [history, setHistory] = useState([]);
  const [currentDate, setCurrentDate] = useState('');

  useEffect(() => {
    const bootstrap = async () => {
      const dates = await syncHistory();
      
      let meta = {};
      if (API_ENDPOINT) {
        meta = await fetch(`${API_ENDPOINT}/current_config`).then(r => r.json()).catch(() => ({}));
      }
      
      const start = (dates && dates.includes(meta.target_date)) 
        ? meta.target_date 
        : (dates?.[0] || meta.target_date || new Date().toISOString().split('T')[0]);
        
      setCurrentDate(start);
      fetchResults(start);
    };
    bootstrap();
  }, []);

  const syncHistory = async () => {
    try {
      const url = API_ENDPOINT ? `${API_ENDPOINT}/history` : '/results/history.json';
      const res = await fetch(url);
      const { dates } = await res.json();
      setHistory(dates || []);
      return dates;
    } catch (e) {
      console.debug("History discovery failed");
      return [];
    }
  };

  const executeScan = async () => {
    setViewState({ loading: true, label: 'Market Scanning...' });
    try {
      await fetch(`${API_ENDPOINT}/scan`, { method: 'POST' });
      const timer = setInterval(async () => {
        const status = await fetch(`${API_ENDPOINT}/status`).then(r => r.json());
        setProgress({ current: status.progress, total: status.total });
        if (status.data?.length) setData(status.data);
        if (status.status === 'complete') {
          clearInterval(timer);
          setViewState({ loading: false, label: 'Sync Complete' });
          syncHistory();
        }
      }, 2000);
    } catch (e) {
      setViewState({ loading: false, label: 'Connection Error' });
    }
  };

  const fetchResults = async (date) => {
    const target = date || currentDate;
    setViewState({ loading: true, label: `Syncing ${target}` });
    
    if (API_ENDPOINT) {
      try {
        const res = await fetch(`${API_ENDPOINT}/load_csv`, { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ date: target })
        });
        
        if (res.ok) {
          const payload = await res.json();
          setData(payload.data || []);
          setProgress({ current: payload.count, total: payload.count });
          setCurrentDate(payload.date);
          setViewState({ loading: false, label: `Viewing ${target}` });
          return;
        }

        if (res.status === 404) {
          const context = await res.json();
          if (context.is_future) return executeScan();
        }
      } catch (e) {
        console.debug("Local API fetch failed");
      }
    }

    await fetchStatic(target);
    setViewState(v => ({ ...v, loading: false }));
  };

  const fetchStatic = async (date) => {
    try {
      const raw = await fetch(`/results/trend_template_results_${date}.csv`).then(r => r.text());
      const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
      if (!lines.length) return;
      
      const head = lines[0];
      const cols = head.split(',').map(c => c.trim().toLowerCase());
      
      const rows = lines.slice(1).map(line => {
        const vals = [];
        let current = '';
        let inQuotes = false;
        for (let j = 0; j < line.length; j++) {
          const char = line[j];
          if (char === '"') {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            vals.push(current.trim());
            current = '';
          } else {
            current += char;
          }
        }
        vals.push(current.trim());

        return cols.reduce((acc, col, i) => {
          let v = vals[i] || '';
          if (col === 'points') {
            try { 
              let cleanVal = v;
              if (cleanVal.startsWith('"') && cleanVal.endsWith('"')) {
                cleanVal = cleanVal.slice(1, -1);
              }
              acc[col] = JSON.parse(cleanVal.replace(/'/g, '"')); 
            } catch { 
              acc[col] = v; 
            }
          } else if (['price', 'score'].includes(col)) {
            acc[col] = parseFloat(v);
          } else {
            acc[col] = v;
          }
          return acc;
        }, {});
      });

      setData(rows);
      setCurrentDate(date);
    } catch (e) {
      console.error("Static CSV parsing failed:", e);
      setData([]);
    }
  };

  const exportSpreadsheet = () => {
    if (!data.length) return;
    const ws = XLSX.utils.json_to_sheet(data.map(item => ({
      ...item,
      points: Array.isArray(item.points) ? item.points.join(', ') : item.points
    })));
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Trend Analysis");
    XLSX.writeFile(wb, `scan_${currentDate}.xlsx`);
  };

  const filtered = useMemo(() => {
    return data
      .filter(s => s && s.ticker && s.ticker.toLowerCase().includes(query.toLowerCase()))
      .sort((a, b) => (b.score || 0) - (a.score || 0));
  }, [data, query]);

  const activeScan = progress.current > 0 && progress.current < progress.total;

  return (
    <div className="dashboard full-view">
      <AnimatePresence>
        {viewState.loading && !data.length && (
          <motion.div className="loading-overlay" exit={{ opacity: 0 }}>
            <div className="loading-content">
              <BarChart3 className="neon-text animate-pulse" size={64} />
              <h2 className="neon-text">Refreshing Data</h2>
              <p>Fetching latest technical signals...</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <header className="main-header">
        <div className="branding">
          <TrendingUp className="neon-text" size={32} />
          <div>
            <p className="subtitle">Trend Template Engine</p>
          </div>
        </div>

        <div className="actions">
          <div className="search-container">
            <Search size={18} />
            <input 
              type="text" 
              placeholder="Search ticker..." 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="history-picker">
            <Calendar size={18} />
            <select value={currentDate} onChange={(e) => fetchResults(e.target.value)}>
              {history.map(d => <option key={d} value={d}>{d}</option>)}
              {!history.includes(currentDate) && <option value={currentDate}>{currentDate}</option>}
            </select>
          </div>
          <button className="btn-secondary" onClick={() => fetchResults()}>
            <RefreshCw size={18} className={viewState.loading ? 'animate-spin' : ''} />
          </button>
          <button className="btn-primary" onClick={exportSpreadsheet} disabled={!data.length}>
            <Download size={18} />
          </button>
        </div>
      </header>

      {activeScan && (
        <div className="prominent-scan-status">
          <div className="status-badge">
            <RefreshCw className="animate-spin" size={16} />
            <span>SCANNING MARKET DATA</span>
          </div>
          <div className="progress-details">
            <span className="count">{progress.current} / {progress.total}</span>
            <span className="percentage">{Math.round((progress.current / progress.total) * 100)}%</span>
          </div>
        </div>
      )}

      <main className="table-container">
        <div className="glass-table-wrapper">
          <table className="stock-table">
            <thead>
              <tr>
                <th className="sticky-col">Ticker</th>
                <th>Price</th>
                <th>Score</th>
                {RULES.map(r => <th key={r.id} className="criteria-header"><span title={r.title}>{r.label}</span></th>)}
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => (
                <motion.tr key={s.ticker} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={s.score === 10 ? 'perfect-row' : ''}>
                  <td className="ticker-cell sticky-col"><span className="ticker-label">{s.ticker}</span></td>
                  <td>${s.price.toFixed(2)}</td>
                  <td><div className={`score-badge score-${s.score}`}>{s.score}</div></td>
                  {s.points.map((p, idx) => (
                    <td key={idx} className="criteria-cell">
                      <div className={`criteria-indicator ${p ? 'pass' : 'fail'}`}>
                        {p ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                      </div>
                    </td>
                  ))}
                </motion.tr>
              ))}
            </tbody>
          </table>
          {!filtered.length && !viewState.loading && (
            <div className="empty-state"><Info size={48} /><p>No matches found</p></div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
