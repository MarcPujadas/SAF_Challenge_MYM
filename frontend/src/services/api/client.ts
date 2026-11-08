import { NativeModules, Platform } from 'react-native';
import type { ApiEnvelope, ApiErrorCode } from './types';

export class ApiError extends Error {
  code: ApiErrorCode;
  constructor(code: ApiErrorCode, message: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
  }
}
type Method = 'GET' | 'POST' | 'DELETE';
type RequestOptions = {
  query?: Record<string, string>;
  body?: unknown;
};

/**
 * Expo Web on the same PC: loopback is correct.
 * Expo Go on a physical device: loopback points to the DEVICE, not Windows.
 * If the Metro bundle exposes its LAN hostname, use that PC IP for the API.
 * Explicit remote EXPO_PUBLIC_API_URL always wins.
 */
export function getApiOrigin(): string {
  const configured = (process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000').trim().replace(/\/+$/, '');
  const isLoopback = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/i.test(configured);
  if (!isLoopback) return configured;

  if (Platform.OS === 'web') {
    // When viewing Expo Web from another machine, localhost would point to that machine.
    if (typeof window !== 'undefined' && window.location.hostname &&
        !['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      return `http://${window.location.hostname}:8000`;
    }
    return configured;
  }

  const bundleUrl: unknown = NativeModules?.SourceCode?.scriptURL;
  if (typeof bundleUrl === 'string') {
    try {
      const host = new URL(bundleUrl).hostname;
      if (host && !['localhost', '127.0.0.1', '10.0.2.2'].includes(host)) {
        return `http://${host}:8000`;
      }
    } catch {
      // The native packager may return a file:// URI or another non-network URL.
    }
  }

  // On a stock Android emulator, 10.0.2.2 reaches the host PC.
  if (Platform.OS === 'android') return 'http://10.0.2.2:8000';
  return configured;
}

function buildQuery(query?: Record<string, string>): string {
  if (!query) return '';
  const parts = Object.entries(query).map(
    ([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
  );
  return parts.length > 0 ? `?${parts.join('&')}` : '';
}

export async function request<T>(
  method: Method,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const origin = getApiOrigin();
  const url = origin + '/api/v1' + path + buildQuery(options.query);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  let response: Response;
  try {
    response = await fetch(url, {
      signal: controller.signal,
      method,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (err) {
    const detail = err instanceof Error ? err.message : String(err);
    const hint = Platform.OS === 'web'
      ? 'Comprova que la web i FastAPI s\'executen al mateix PC.'
      : 'Si es un telefon, ha de ser a la mateixa Wi-Fi i el backend ha d\'escoltar a 0.0.0.0.';
    throw new ApiError(
      'NETWORK_ERROR',
      `No es pot accedir a ${origin}/api/v1 (URL: ${url}). ${detail}. ${hint}`,
    );
  } finally {
    clearTimeout(timeout);
  }

  let json: ApiEnvelope<T>;
  try {
    json = (await response.json()) as ApiEnvelope<T>;
  } catch {
    // This used to be reported as 'no connection', even for HTTP 500.
    throw new ApiError(
      'SERVER_ERROR',
      `El servidor respon HTTP ${response.status}, però no retorna JSON vàlid a ${url}. Revisa la finestra FastAPI.`,
    );
  }
  if (json === null || typeof json !== 'object' || typeof json.success !== 'boolean') {
    throw new ApiError(
      'SERVER_ERROR',
      `Resposta inesperada de l'API (HTTP ${response.status}) a ${url}. Comprova que sigui el backend de SAFi.`,
    );
  }
  if (!response.ok || !json.success) {
    throw new ApiError(
      json.error?.code ?? 'SERVER_ERROR',
      json.error?.message ?? `Error HTTP ${response.status} a ${url}`,
    );
  }
  return json.data as T;
}
