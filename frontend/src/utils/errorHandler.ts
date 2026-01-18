/**
 * Error handling utilities
 */

/**
 * Extract error message from unknown error type
 * Handles Error instances, string errors, and fallback messages
 */
export function getErrorMessage(error: unknown, fallbackMessage: string): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return fallbackMessage;
}

/**
 * Safely parse API error responses (handles JSON, HTML, and text).
 * Prevents crashes when backend returns non-JSON (e.g., 500 HTML error pages).
 *
 * @param response - Fetch Response object
 * @returns Human-readable error message
 */
export async function parseApiError(response: Response): Promise<string> {
  try {
    // 尝试解析 JSON
    const data = await response.json();
    // 优先取 detail (FastAPI 标准), 其次 message, 最后 stringify 整个对象
    return data.detail || data.message || JSON.stringify(data);
  } catch {
    // JSON 解析失败,回退到文本 (处理 500 HTML 页面)
    try {
      const text = await response.text();
      // 截取前 100 字符避免过长 HTML
      return text.slice(0, 100) || response.statusText;
    } catch {
      return response.statusText;
    }
  }
}

/**
 * Log error to console in production (can be extended for error tracking services)
 */
export function logError(context: string, error: unknown): void {
  if (import.meta.env.PROD) {
    console.error(`[${context}]`, error);
  }
}
