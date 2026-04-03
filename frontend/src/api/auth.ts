import { publicClient } from "./client";
import type { TokenPair } from "@/types";

export const authApi = {
  register: async (email: string, password: string): Promise<TokenPair> => {
    const { data } = await publicClient.post<TokenPair>("/auth/register", { email, password });
    return data;
  },

  login: async (email: string, password: string): Promise<TokenPair> => {
    const { data } = await publicClient.post<TokenPair>("/auth/login", { email, password });
    return data;
  },

  refresh: async (refreshToken: string): Promise<TokenPair> => {
    const { data } = await publicClient.post<TokenPair>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await publicClient.post("/auth/logout", { refresh_token: refreshToken });
  },
};
