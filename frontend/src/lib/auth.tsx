"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { userApi, ApiError } from "./api";
import type { User, UserWithMemberships } from "./types";

// ── Types ──────────────────────────────────────────────────────────

type AuthContextValue = {
  user: UserWithMemberships | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
};

// ── Context ────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ───────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserWithMemberships | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Validate existing token on mount
  useEffect(() => {
    const stored = localStorage.getItem("token");
    if (!stored) {
      setIsLoading(false);
      return;
    }
    setToken(stored);
    userApi
      .getMe()
      .then((me) => {
        setUser(me);
      })
      .catch(() => {
        // Token invalid — clear it
        localStorage.removeItem("token");
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await userApi.login(email, password);
    localStorage.setItem("token", res.token);
    setToken(res.token);
    // Fetch full user with memberships
    const me = await userApi.getMe();
    setUser(me);
  }, []);

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      const res = await userApi.register(email, name, password);
      localStorage.setItem("token", res.token);
      setToken(res.token);
      const me = await userApi.getMe();
      setUser(me);
    },
    [],
  );

  const logout = useCallback(() => {
    userApi.logout().catch(() => {});
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext>
  );
}

// ── Hook ───────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
