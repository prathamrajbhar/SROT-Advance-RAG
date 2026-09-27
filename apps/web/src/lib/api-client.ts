import { toast } from "@/components/ui/toast";
import { API_CONFIG } from "@/config/api";

const API_BASE_URL = API_CONFIG.baseUrl;

let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem("srot_token", token);
    } else {
      localStorage.removeItem("srot_token");
    }
  }
}

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  if (typeof window !== "undefined") {
    accessToken = localStorage.getItem("srot_token");
  }
  return accessToken;
}

export class ApiError extends Error {
  public status: number;
  public detail: string;
  public trace_id?: string;

  constructor(status: number, detail: string, trace_id?: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.trace_id = trace_id;
  }
}

export interface ApiFetchOptions extends RequestInit {
  silentError?: boolean;
  _retry?: boolean;
}

async function requestNewToken(): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
      setAccessToken(null);
      return null;
    }
    const data = await res.json();
    if (data.access_token) {
      setAccessToken(data.access_token);
      return data.access_token;
    }
    setAccessToken(null);
    return null;
  } catch {
    setAccessToken(null);
    return null;
  }
}

export async function silentRefreshToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = requestNewToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export async function apiFetch<T>(
  endpoint: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { silentError, _retry, ...fetchOptions } = options;
  const token = getAccessToken();
  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(fetchOptions.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
    credentials: "include",
  });

  const traceId = response.headers.get("X-Trace-Id") || undefined;

  if (response.status === 204) {
    return {} as T;
  }

  const isAuthEndpoint =
    endpoint.startsWith("/auth/login") ||
    endpoint.startsWith("/auth/register") ||
    endpoint.startsWith("/auth/refresh");

  // Attempt transparent token refresh on 401
  if (response.status === 401 && !isAuthEndpoint && !_retry) {
    const freshToken = await silentRefreshToken();
    if (freshToken) {
      return apiFetch<T>(endpoint, {
        ...options,
        _retry: true,
      });
    }
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.title || errorDetail;
    } catch {
      errorDetail = response.statusText || "Request failed";
    }

    if (response.status === 401 && typeof window !== "undefined") {
      setAccessToken(null);
    }

    const err = new ApiError(response.status, errorDetail, traceId);

    if (!silentError && typeof window !== "undefined") {
      const title = response.status === 401 ? "Authentication Required" : `Error ${response.status}`;
      toast.error(errorDetail, title, traceId);
    }

    throw err;
  }

  return response.json();
}

