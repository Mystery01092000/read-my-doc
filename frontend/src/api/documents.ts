import type { Document, PaginatedResponse } from "@/types";
import { createApiClient } from "./client";
import { useAuthStore } from "@/store/useAuthStore";

function client() {
  return createApiClient(() => useAuthStore.getState().accessToken);
}

export const documentsApi = {
  list: async (page = 1, limit = 20): Promise<PaginatedResponse<Document>> => {
    const { data } = await client().get<PaginatedResponse<Document>>("/documents", {
      params: { page, limit },
    });
    return data;
  },

  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await client().post<Document>("/documents", formData);
    return data;
  },

  get: async (id: string): Promise<Document> => {
    const { data } = await client().get<Document>(`/documents/${id}`);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await client().delete(`/documents/${id}`);
  },
};
