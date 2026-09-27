import { toast } from "@/components/ui/toast";
import { API_CONFIG } from "@/config/api";

const API_BASE_URL = API_CONFIG.baseUrl;

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
}

export async function apiFetch<T>(
  endpoint: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { silentError, ...fetchOptions } = options;
  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (!(fetchOptions.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  const traceId = response.headers.get("X-Trace-Id") || undefined;

  if (response.status === 204) {
    return {} as T;
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.title || errorDetail;
    } catch {
      errorDetail = response.statusText || "Request failed";
    }

    const err = new ApiError(response.status, errorDetail, traceId);

    if (!silentError && typeof window !== "undefined") {
      toast.error(errorDetail, `Error ${response.status}`, traceId);
    }

    throw err;
  }

  return response.json();
}
