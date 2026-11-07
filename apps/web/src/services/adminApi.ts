// Local-only admin transport. Credentials live in component memory, never in storage or URLs.
export type PilotPhase = 'idle' | 'preparing' | 'ready' | 'training' | 'evaluating' | 'complete' | 'failed';
export type WandbMode = 'online' | 'offline' | null;

export interface TrainingRun {
  runId: string | null;
  phase: PilotPhase;
  datasetVersion: string | null;
  featureSchemaVersion: string | null;
  sampleTotal: number;
  accepted: number;
  epoch: number | null;
  epochs: number | null;
  metrics: { accuracy: number | null; macroF1: number | null } | null;
  wandbRunId: string | null;
  wandbMode: WandbMode;
  wandbUrl: string | null;
  updatedAt: string | null;
  failed: boolean;
}

export type AdminErrorKind = 'disabled' | 'unauthorized' | 'conflict' | 'invalid-input'
  | 'unavailable' | 'timeout' | 'invalid-response' | 'network' | 'cancelled';

export class AdminApiError extends Error {
  constructor(public readonly kind: AdminErrorKind, public readonly status?: number) {
    super(kind);
    this.name = 'AdminApiError';
  }
}

const object = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === 'object' && !Array.isArray(value);
const count = (value: unknown): value is number =>
  typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const optionalString = (value: unknown): string | null =>
  typeof value === 'string' && value.trim() ? value : null;
const phases: PilotPhase[] = ['idle', 'preparing', 'ready', 'training', 'evaluating', 'complete', 'failed'];

function safeWandbUrl(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password) return null;
    if (url.hostname === 'wandb.ai' && /^\/[\w.-]+\/[\w.-]+\/runs\/[\w-]+\/?$/.test(url.pathname)) return url.href;
    if (url.hostname === 'forge.coreweave.com' && /^\/wandb\/[\w.-]+\/[\w.-]+\/runs\/[\w-]+\/?$/.test(url.pathname)) return url.href;
  } catch { /* Invalid or untrusted URL: show run ID instead. */ }
  return null;
}

function parseTimestamp(value: unknown): string | null {
  if (typeof value === 'string' && Number.isFinite(Date.parse(value))) return new Date(value).toISOString();
  // A historical local pilot runner emitted Unix seconds.
  if (typeof value === 'number' && Number.isFinite(value) && value >= 0) {
    const date = new Date(value < 1e11 ? value * 1000 : value);
    if (Number.isFinite(date.getTime())) return date.toISOString();
  }
  return null;
}

function parseRun(raw: unknown): TrainingRun {
  if (!object(raw) || !phases.includes(raw.phase as PilotPhase)) {
    throw new AdminApiError('invalid-response');
  }
  const sampleTotal = count(raw.sampleTotal) ? raw.sampleTotal : 0;
  const accepted = count(raw.accepted) && raw.accepted <= sampleTotal ? raw.accepted : 0;
  const metrics = object(raw.metrics) ? {
    accuracy: typeof raw.metrics.accuracy === 'number' && raw.metrics.accuracy >= 0 && raw.metrics.accuracy <= 1
      ? raw.metrics.accuracy : null,
    macroF1: typeof raw.metrics.macroF1 === 'number' && raw.metrics.macroF1 >= 0 && raw.metrics.macroF1 <= 1
      ? raw.metrics.macroF1 : null,
  } : null;
  const wandbUrl = safeWandbUrl(raw.wandbUrl);
  const mode = raw.wandbMode === 'offline' ? 'offline' : raw.wandbMode === 'online' || wandbUrl ? 'online' : null;
  return {
    runId: optionalString(raw.runId) ?? optionalString(raw.id),
    phase: raw.phase as PilotPhase,
    datasetVersion: optionalString(raw.datasetVersion),
    featureSchemaVersion: optionalString(raw.featureSchemaVersion),
    sampleTotal, accepted,
    epoch: count(raw.epoch) ? raw.epoch : null,
    epochs: count(raw.epochs) && raw.epochs > 0 ? raw.epochs : null,
    metrics,
    wandbRunId: optionalString(raw.wandbRunId),
    wandbMode: mode,
    wandbUrl,
    updatedAt: parseTimestamp(raw.updatedAt),
    // Avoid rendering arbitrary backend error strings, which may contain paths or traces.
    failed: raw.phase === 'failed',
  };
}

function kindFromStatus(status: number): AdminErrorKind {
  if (status === 401) return 'unauthorized';
  if (status === 404) return 'disabled';
  if (status === 409) return 'conflict';
  if (status === 503) return 'unavailable';
  if (status === 504) return 'timeout';
  if (status >= 400 && status < 500) return 'invalid-input';
  return 'unavailable';
}

export function adminErrorMessage(error: unknown): string {
  if (!(error instanceof AdminApiError)) return 'Không thể thực hiện yêu cầu admin. Vui lòng thử lại.';
  const messages: Record<AdminErrorKind, string> = {
    disabled: 'Công cụ admin chưa được bật trên backend (404).',
    unauthorized: 'Mã admin không đúng hoặc đã hết hiệu lực (401). Vui lòng nhập lại.',
    conflict: 'Đang có một công việc khác chạy (409). Hãy tải lại trạng thái.',
    'invalid-input': 'Dữ liệu gửi lên không hợp lệ. Kiểm tra video hoặc bản bàn giao (4xx).',
    unavailable: 'Worker hoặc môi trường backend chưa sẵn sàng (503).',
    timeout: 'Kiểm tra clip quá thời gian cho phép (504).',
    'invalid-response': 'Backend trả về dữ liệu admin không đúng định dạng.',
    network: 'Không thể kết nối đến backend. Kiểm tra kết nối mạng.',
    cancelled: 'Đã hủy yêu cầu.',
  };
  return messages[error.kind];
}

async function request(token: string, path: string, method: 'GET' | 'POST', signal?: AbortSignal, body?: FormData) {
  try {
    const response = await fetch(`/api/admin/${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'omit',
      cache: 'no-store',
      ...(signal ? { signal } : {}),
      ...(body ? { body } : {}),
    });
    if (!response.ok) throw new AdminApiError(kindFromStatus(response.status), response.status);
    return response;
  } catch (error) {
    if (error instanceof AdminApiError) throw error;
    if (signal?.aborted) throw new AdminApiError('cancelled');
    throw new AdminApiError('network');
  }
}

async function json(response: Response): Promise<unknown> {
  try { return await response.json() as unknown; }
  catch { throw new AdminApiError('invalid-response'); }
}

export const MAX_ADMIN_CLIP_BYTES = 100 * 1024 * 1024;

export function createAdminApi(token: string) {
  return {
    async inspect(video: File, signal?: AbortSignal): Promise<Blob> {
      if (!/\.(mp4|webm)$/i.test(video.name) || video.size === 0 || video.size > MAX_ADMIN_CLIP_BYTES) {
        throw new AdminApiError('invalid-input');
      }
      const form = new FormData();
      form.append('video', video);
      const response = await request(token, 'inspect', 'POST', signal, form);
      const blob = await response.blob();
      if (!blob.size) throw new AdminApiError('invalid-response');
      return blob;
    },
    async pilot(signal?: AbortSignal): Promise<TrainingRun> {
      return parseRun(await json(await request(token, 'pilot', 'GET', signal)));
    },
    async history(signal?: AbortSignal): Promise<TrainingRun[]> {
      const data = await json(await request(token, 'pilot/history', 'GET', signal));
      if (!Array.isArray(data)) throw new AdminApiError('invalid-response');
      return data.map(parseRun).sort((a, b) =>
        (b.updatedAt ? Date.parse(b.updatedAt) : 0) - (a.updatedAt ? Date.parse(a.updatedAt) : 0));
    },
    async prepare(signal?: AbortSignal): Promise<TrainingRun> {
      return parseRun(await json(await request(token, 'pilot/prepare', 'POST', signal)));
    },
    async train(signal?: AbortSignal): Promise<TrainingRun> {
      return parseRun(await json(await request(token, 'pilot/train', 'POST', signal)));
    },
  };
}
