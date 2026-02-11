import { useAuth } from "@clerk/clerk-react";

export type PageMeta = {
  limit: number;
  offset: number;
  total: number;
  has_next: boolean;
  order_by: string[];
};

export type Device = {
  id: string;
  mac_address: string;
  status: "active" | "retired";
  created_at: string;
  updated_at: string;
  version: number;
};

export type ProjectedDevice = {
  id: string;
  mac_address: string;
  status: "active" | "retired";
  owner_email: string | null;
  created_at: string;
  updated_at: string;
  version: number;
};

export type DataResponse<T> = { data: T };
export type ListResponse<T> = { data: T[]; page: PageMeta };

const baseUrl = import.meta.env.VITE_API_URL as string;

export function useApi() {
  const { getToken } = useAuth();

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await getToken({ template: "device-management" });
    if (!token) throw new Error("Missing auth token");

    const res = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        "content-type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(init?.headers ?? {}),
      },
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(body || `Request failed: ${res.status}`);
    }
    return res.json();
  }

  return { request };
}
