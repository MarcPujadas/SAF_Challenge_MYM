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

function baseUrl(): string {
  // Expo nomes substitueix EXPO_PUBLIC_* si s'escriu exactament aixi.
  const url = process.env.EXPO_PUBLIC_API_URL;
  if (!url) {
    throw new Error(
      'Falta EXPO_PUBLIC_API_URL. Copia frontend/.env.example a frontend/.env i reinicia Expo.',
    );
  }
  return url.replace(/\/+$/, '') + '/api/v1';
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
  const url = baseUrl() + path + buildQuery(options.query);

  let response: Response;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    response = await fetch(url, {
      signal: controller.signal,
      method,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (err) {
    throw new ApiError('NETWORK_ERROR', `No s'ha pogut connectar amb el servidor: ${String(err)}`);
  } finally {
    clearTimeout(timeout);
  }

  let json: ApiEnvelope<T>;
  try {
    json = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new ApiError('NETWORK_ERROR', `Resposta no valida del servidor (HTTP ${response.status}).`);
  }

  if (json === null || typeof json !== 'object' || typeof json.success !== 'boolean') {
    throw new ApiError('NETWORK_ERROR', `Resposta sense el format esperat (HTTP ${response.status}).`);
  }

  if (!json.success) {
    throw new ApiError(
      json.error?.code ?? 'UNKNOWN_ERROR',
      json.error?.message ?? 'Error desconegut del servidor.',
    );
  }

  return json.data as T;
}
