// Single source of truth for the JWT pair. Persisted to localStorage so a
// page reload keeps the session, and exposed through a tiny pub/sub so the
// AuthContext can react when tokens change (e.g. cleared after a failed
// refresh).

const ACCESS_KEY = 'discovery.accessToken';
const REFRESH_KEY = 'discovery.refreshToken';

export interface Tokens {
  accessToken: string;
  refreshToken: string;
}

type Listener = () => void;
const listeners = new Set<Listener>();

export function getTokens(): Tokens | null {
  const accessToken = localStorage.getItem(ACCESS_KEY);
  const refreshToken = localStorage.getItem(REFRESH_KEY);
  if (!accessToken || !refreshToken) return null;
  return { accessToken, refreshToken };
}

export function setTokens(tokens: Tokens): void {
  localStorage.setItem(ACCESS_KEY, tokens.accessToken);
  localStorage.setItem(REFRESH_KEY, tokens.refreshToken);
  listeners.forEach((l) => l());
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  listeners.forEach((l) => l());
}

export function onTokensChanged(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
