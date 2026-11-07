import { useCallback, useEffect, useState } from 'react';
import {
  AdminApiError, adminErrorMessage, createAdminApi,
  type PilotPhase, type TrainingRun,
} from '../../services/adminApi';

const phaseText: Record<PilotPhase, string> = {
  idle: 'Chưa có lần chạy pilot',
  preparing: 'Đang kiểm tra dữ liệu và trích xuất đặc trưng',
  ready: 'Dữ liệu đã sẵn sàng để huấn luyện',
  training: 'Đang huấn luyện pilot',
  evaluating: 'Đang đánh giá pilot',
  complete: 'Đã hoàn thành pilot',
  failed: 'Lần chạy pilot gặp lỗi',
};

function percent(value: number | null) {
  return value === null ? 'Chưa có' : new Intl.NumberFormat('vi-VN', {
    style: 'percent', maximumFractionDigits: 1,
  }).format(value);
}

function RunDetails({ run }: { run: TrainingRun }) {
  return <div className="admin-run-details">
    <dl>
      <div><dt>Mã job</dt><dd>{run.runId ?? 'Chưa có'}</dd></div>
      <div><dt>Dữ liệu</dt><dd>{run.datasetVersion ?? 'Chưa xác nhận'}</dd></div>
      <div><dt>Schema</dt><dd>{run.featureSchemaVersion ?? 'Chưa xác nhận'}</dd></div>
      <div><dt>Clip hợp lệ</dt><dd>{run.accepted} / {run.sampleTotal}</dd></div>
      <div><dt>Epoch</dt><dd>{run.epoch ?? '—'} / {run.epochs ?? '—'}</dd></div>
    </dl>
    {run.metrics && <p className="admin-metrics">Accuracy: <strong>{percent(run.metrics.accuracy)}</strong>
      {' · '}Macro-F1: <strong>{run.metrics.macroF1?.toFixed(3) ?? 'Chưa có'}</strong></p>}
    {run.failed && <p className="admin-warning">Worker đã báo lỗi. Hãy kiểm tra log an toàn trên máy backend.</p>}
    {(run.wandbMode || run.wandbRunId) && <div className="admin-wandb">
      <strong>Weights &amp; Biases</strong>
      <span>{run.wandbMode === 'offline' ? ' · Log offline' : run.wandbUrl ? ' · Online' : ' · Chưa có liên kết'}</span>
      {run.wandbRunId && <p>Run ID: <code>{run.wandbRunId}</code></p>}
      {run.wandbUrl && <p><a href={run.wandbUrl} target="_blank" rel="noopener noreferrer">Mở biểu đồ W&amp;B ↗</a></p>}
    </div>}
    {run.updatedAt && <time dateTime={run.updatedAt}>Cập nhật: {new Date(run.updatedAt).toLocaleString('vi-VN')}</time>}
  </div>;
}

interface PilotPanelProps {
  token: string;
  onUnauthorized: () => void;
}

export default function PilotPanel({ token, onUnauthorized }: PilotPanelProps) {
  const [run, setRun] = useState<TrainingRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<'prepare' | 'train' | null>(null);
  const [error, setError] = useState('');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [history, setHistory] = useState<TrainingRun[]>([]);
  const [historyError, setHistoryError] = useState('');

  const load = useCallback(async (signal?: AbortSignal, preserveError = false) => {
    try {
      const status = await createAdminApi(token).pilot(signal);
      if (signal?.aborted) return;
      setRun(status);
      if (!preserveError) setError('');
    } catch (reason) {
      if (signal?.aborted || (reason instanceof AdminApiError && reason.kind === 'cancelled')) return;
      if (reason instanceof AdminApiError && reason.kind === 'unauthorized') onUnauthorized();
      setError(adminErrorMessage(reason));
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [token, onUnauthorized]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const active = run?.phase === 'preparing' || run?.phase === 'training' || run?.phase === 'evaluating';
  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    const timer = window.setInterval(() => void load(controller.signal), 4000);
    return () => { window.clearInterval(timer); controller.abort(); };
  }, [active, load]);

  async function start(next: 'prepare' | 'train') {
    if (action || active) return;
    setAction(next);
    setError('');
    try {
      const api = createAdminApi(token);
      const status = next === 'prepare' ? await api.prepare() : await api.train();
      setRun(status);
    } catch (reason) {
      if (reason instanceof AdminApiError && reason.kind === 'unauthorized') onUnauthorized();
      setError(adminErrorMessage(reason));
      if (reason instanceof AdminApiError && reason.kind === 'conflict') void load(undefined, true);
    } finally { setAction(null); }
  }

  async function toggleHistory() {
    if (historyOpen) { setHistoryOpen(false); return; }
    setHistoryOpen(true);
    setHistoryLoading(true);
    setHistoryError('');
    try { setHistory(await createAdminApi(token).history()); }
    catch (reason) {
      if (reason instanceof AdminApiError && reason.kind === 'unauthorized') onUnauthorized();
      setHistoryError(adminErrorMessage(reason));
    } finally { setHistoryLoading(false); }
  }

  return <section className="admin-card" aria-label="Huấn luyện pilot">
    <div className="admin-card-heading">
      <h2>Huấn luyện pilot</h2>
      <button type="button" onClick={() => { setLoading(true); void load(); }} disabled={loading || !!action}>Tải lại trạng thái</button>
    </div>
    <p className="admin-note">Kết quả pilot chỉ dùng để đánh giá nội bộ, không tự cho phép phát hành demo.</p>
    {loading && !run && <p role="status">Đang đọc trạng thái pilot…</p>}
    {error && <p role="alert" className="admin-warning">{error}</p>}
    {run && <>
      <p role="status" className="admin-phase">{phaseText[run.phase]}</p>
      <RunDetails run={run} />
      {active && <p className="admin-note">Job đang chạy. Trạng thái được cập nhật tự động mỗi 4 giây.</p>}
      <div className="admin-actions">
        <button type="button" disabled={active || !!action || loading || run.phase === 'ready'}
          onClick={() => void start('prepare')}>{action === 'prepare' ? 'Đang chuẩn bị…' : 'Chạy preflight'}</button>
        <button type="button" className="admin-primary" disabled={run.phase !== 'ready' || !!action || loading}
          onClick={() => void start('train')}>{action === 'train' ? 'Đang gửi…' : 'Bắt đầu train'}</button>
      </div>
    </>}
    <div className="admin-history-controls">
      <button type="button" onClick={() => void toggleHistory()}>{historyOpen ? 'Ẩn lịch sử' : 'Xem lịch sử train'}</button>
    </div>
    {historyOpen && <section aria-label="Lịch sử train">
      <h3>Lịch sử train</h3>
      {historyLoading && <p role="status">Đang tải lịch sử…</p>}
      {historyError && <p role="alert" className="admin-warning">{historyError}</p>}
      {!historyLoading && !historyError && history.length === 0 && <p>Chưa có lần chạy nào.</p>}
      {!historyLoading && !historyError && <ol className="admin-history">{history.map((item, index) =>
        <li key={`${item.runId ?? 'idle'}-${index}`}>
          <h4>{phaseText[item.phase]}</h4>
          <RunDetails run={item} />
        </li>)}</ol>}
    </section>}
  </section>;
}
