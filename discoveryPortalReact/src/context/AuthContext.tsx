import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { authApi } from '../api/services';
import { clearTokens, getTokens, onTokensChanged } from '../api/tokenStore';
import type { User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Bootstrap: if we have tokens, resolve the current user. Re-runs whenever
  // the token store changes (login, logout, or a failed refresh clearing it).
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!getTokens()) {
        if (!cancelled) {
          setUser(null);
          setIsLoading(false);
        }
        return;
      }
      try {
        const me = await authApi.me();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    bootstrap();
    const unsubscribe = onTokensChanged(() => {
      setIsLoading(true);
      bootstrap();
    });
    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      async login(email, password) {
        await authApi.login(email, password);
        setUser(await authApi.me());
      },
      async register(email, password, displayName) {
        await authApi.register({ email, password, display_name: displayName });
        await authApi.login(email, password);
        setUser(await authApi.me());
      },
      async logout() {
        const tokens = getTokens();
        if (tokens) {
          try {
            await authApi.logout(tokens.refreshToken);
          } catch {
            // Revocation is best-effort; clear locally regardless.
          }
        }
        clearTokens();
        setUser(null);
      },
    }),
    [user, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
