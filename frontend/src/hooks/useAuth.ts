import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/useAuthStore";

export function useAuth() {
  const { setTokens, clearTokens, refreshToken } = useAuthStore();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokens = await authApi.login(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/documents");
    } catch {
      setError("Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokens = await authApi.register(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/documents");
    } catch {
      setError("Registration failed. Email may already be in use.");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch {
        // best-effort
      }
    }
    clearTokens();
    navigate("/login");
  };

  return { login, register, logout, isLoading, error };
}
