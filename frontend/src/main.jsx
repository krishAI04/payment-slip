import { StrictMode, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API = 'http://localhost:8000/api';
const download = (blob, name) => { const url = URL.createObjectURL(blob); Object.assign(document.createElement('a'), { href: url, download: name }).click(); URL.revokeObjectURL(url); };

function App() {
  const input = useRef();
  const [file, setFile] = useState();
  const [info, setInfo] = useState();
  const [bonusOrders, setBonusOrders] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function inspect(next) {
    setError(''); setInfo(); setBonusOrders({});
    if (!next) return;
    if (!/\.xls(x)?$/i.test(next.name)) return setError('Choose an Excel .xlsx or .xls file.');
    setFile(next); setBusy(true);
    const body = new FormData(); body.append('file', next);
    try {
      const response = await fetch(`${API}/inspect`, { method: 'POST', body });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || data.detail || 'We could not read this file.');
      setInfo(data);
    } catch (event) { setError(event.message); setFile(); } finally { setBusy(false); }
  }

  function addUpload(body) { body.append('file', file); body.append('bonus_work_orders', JSON.stringify(Object.keys(bonusOrders).filter(order => bonusOrders[order]))); }
  async function generate() {
    setBusy(true); setError(''); const body = new FormData(); addUpload(body);
    try {
      const response = await fetch(`${API}/generate`, { method: 'POST', body });
      if (!response.ok) { const data = await response.json(); throw new Error(data.detail?.message || data.detail || 'Generation failed.'); }
      download(await response.blob(), 'payment_slips.zip');
    } catch (event) { setError(event.message); } finally { setBusy(false); }
  }

  async function one(workOrder) {
    setBusy(true); const body = new FormData(); body.append('file', file); body.append('use_bonus', Boolean(bonusOrders[workOrder]));
    try {
      const response = await fetch(`${API}/work-order-pdf?work_order=${encodeURIComponent(workOrder)}`, { method: 'POST', body });
      if (!response.ok) throw new Error('Unable to create that PDF.');
      download(await response.blob(), `${workOrder.replace(/[\\/:*?"<>|]/g, '-')}.pdf`);
    } catch (event) { setError(event.message); } finally { setBusy(false); }
  }

  return <main><section className="hero"><p className="eyebrow">DOCUMENT UTILITY</p><h1>Payment Slip Generator</h1><p>Upload your FORM-XVII Excel file. We group every employee by Work Order and create ready-to-download PDFs.</p></section><section className="card"><h2>1. Upload your Excel file</h2><input ref={input} className="sr" id="upload" type="file" accept=".xlsx,.xls" onChange={event => inspect(event.target.files?.[0])}/><label className="dropzone" htmlFor="upload" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); inspect(event.dataTransfer.files?.[0]); }}><strong>Drop your Excel file here</strong><span>or choose a .xlsx or .xls file from your computer</span><b>Choose Excel file</b></label>{busy && <p className="status" role="status">Processing your file...</p>}{error && <p className="error" role="alert">{error}</p>}{info && <><div className="summary"><div><strong>{file.name}</strong><span>Excel file ready</span></div><div><strong>{info.records}</strong><span>payment slips found</span></div><div><strong>{info.workOrders}</strong><span>Work Orders found</span></div></div><h2>2. Choose the wording per Work Order</h2><p className="hint">Tick a box only when “Special Reward” should be shown as “Bonus” on that Work Order’s payment slips.</p><div className="orders">{info.orders.map(order => <div className="order" key={order.workOrder}><label><input type="checkbox" checked={Boolean(bonusOrders[order.workOrder])} onChange={event => setBonusOrders({ ...bonusOrders, [order.workOrder]: event.target.checked })}/><span>{order.workOrder}<small>{order.records} payment slips</small></span></label><button disabled={busy} onClick={() => one(order.workOrder)}>Download PDF</button></div>)}</div><h2>3. Generate</h2><button className="primary" disabled={busy} onClick={generate}>Generate Payment Slips and Download ZIP</button></>}</section><footer>Your information is processed only while the file is being generated.</footer></main>;
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>);
