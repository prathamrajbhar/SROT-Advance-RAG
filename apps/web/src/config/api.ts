/**
 * Application API Configuration
 * Supports server-proxied private API_URL and direct client fallback.
 */
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "/api/v1",
} as const;
