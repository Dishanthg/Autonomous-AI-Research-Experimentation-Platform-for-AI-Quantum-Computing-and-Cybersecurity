import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, setToken } from "../api/client";

interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: CurrentUser | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("rmq_token"));
  const [user, setUser] = useState<CurrentUser | null>(null);

  const loadUser = useCallback(() => {
    api
      .get<CurrentUser>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (isAuthenticated) loadUser();
  }, [isAuthenticated, loadUser]);

  async function login(email: string, password: string) {
    const resp = await api.postForm<{ access_token: string }>("/auth/login", {
      username: email,
      password,
    });
    setToken(resp.access_token);
    setIsAuthenticated(true);
  }

  async function register(email: string, password: string, fullName: string, role: string) {
    await api.post("/auth/register", { email, password, full_name: fullName, role });
  }

  function logout() {
    setToken(null);
    setIsAuthenticated(false);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
