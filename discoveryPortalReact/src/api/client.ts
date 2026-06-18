import { getTokens, setTokens, clearTokens } from './tokenStore';

// All backend routes are same-origin during dev thanks to the Vite proxy, so
// requests use root-relative paths. The auth endpoints already carry the
// `/api/auth` prefix in the path passed by callers.
const AUTH_PATHS = ['/api/auth/token', '/api/auth/register', '/api/auth/refresh'];

export interface ValidationError {
  field: string;
  message: string;
  code?: string | null;
}

/** Normalised error thrown by every request helper. */
export class ApiError extends Error {
  status: number;
  validationErrors?: ValidationError[];

  constructor(status: number, message: string, validationErrors?: ValidationError[]) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.validationErrors = validationErrors;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Override the default JSON content type (used for form-encoded login). */
  rawBody?: BodyInit;
  headers?: Record<string, string>;
  /** Skip attaching the bearer token (auth endpoints). */
  skipAuth?: boolean;
}

/**
 * Pull a human-readable message out of the FastAPI error envelope, which may
 * be `{detail: "..."}`, `{detail: {error, validation_errors}}`, or the
 * register/change-password shape `{error, validation_errors}`.
 */
function parseError(status: number, payload: unknown): ApiError {
  let message = `Request failed (${status})`;
  let validationErrors: ValidationError[] | undefined;

  const detail = (payload as { detail?: unknown })?.detail ?? payload;

  if (typeof detail === 'string') {
    message = detail;
  } else if (detail && typeof detail === 'object') {
    const obj = detail as { error?: string; validation_errors?: ValidationError[] };
    if (obj.error) message = obj.error;
    if (Array.isArray(obj.validation_errors)) {
      validationErrors = obj.validation_errors;
      if (!obj.error && validationErrors.length) {
        message = validationErrors.map((e) => `${e.field}: ${e.message}`).join('; ');
      }
    }
  }

  return new ApiError(status, message, validationErrors);
}

async function readBody(res: Response): Promise<unknown> {
  if (res.status === 204) return null;
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

// Guards against a refresh stampede: concurrent 401s share one refresh call.
let refreshInFlight: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const tokens = getTokens();
  if (!tokens) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokens.refreshToken }),
        });
        if (!res.ok) {
          clearTokens();
          return false;
        }
        const data = (await res.json()) as { access_token: string; refresh_token: string };
        setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token });
        return true;
      } catch {
        clearTokens();
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

async function rawRequest(path: string, opts: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { ...opts.headers };

  if (opts.body !== undefined && !opts.rawBody) {
    headers['Content-Type'] = 'application/json';
  }

  if (!opts.skipAuth) {
    const tokens = getTokens();
    if (tokens) headers['Authorization'] = `Bearer ${tokens.accessToken}`;
  }

  return fetch(path, {
    method: opts.method ?? 'GET',
    headers,
    body: opts.rawBody ?? (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
  });
}

/** Core request helper: attaches auth, transparently refreshes once on 401. */
export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const isAuthPath = AUTH_PATHS.includes(path);

  let res = await rawRequest(path, opts);

  // Transparent refresh-and-retry on expired access token.
  if (res.status === 401 && !opts.skipAuth && !isAuthPath && getTokens()) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      res = await rawRequest(path, opts);
    }
  }

  if (!res.ok) {
    const payload = await readBody(res);
    throw parseError(res.status, payload);
  }

  return (await readBody(res)) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
