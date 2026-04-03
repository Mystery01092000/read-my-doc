import axios, { type AxiosInstance } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";

export function createApiClient(getToken: () => string | null): AxiosInstance {
  const client = axios.create({ baseURL: BASE_URL });

  client.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  return client;
}

// Default unauthenticated client for auth endpoints
export const publicClient = axios.create({ baseURL: BASE_URL });
