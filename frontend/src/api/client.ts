import axios, { type AxiosInstance } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function transformKeys(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(transformKeys);
  if (obj !== null && typeof obj === "object") {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [
        snakeToCamel(k),
        transformKeys(v),
      ])
    );
  }
  return obj;
}

function addCamelCaseInterceptor(client: AxiosInstance): void {
  client.interceptors.response.use((response) => {
    response.data = transformKeys(response.data);
    return response;
  });
}

export function createApiClient(getToken: () => string | null): AxiosInstance {
  const client = axios.create({ baseURL: BASE_URL });

  client.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  addCamelCaseInterceptor(client);
  return client;
}

// Default unauthenticated client for auth endpoints
export const publicClient = axios.create({ baseURL: BASE_URL });
addCamelCaseInterceptor(publicClient);
