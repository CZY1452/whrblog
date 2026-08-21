/**
 * API 客户端封装
 * - 自动附加 CSRF Token（cookie）
 * - 统一错误提取
 * - 全局 401 拦截，跳转登录页
 */

/**
 * 全局 401 拦截：未登录时跳转 /login
 * 避免在循环中重复跳转
 */
let _redirecting401 = false;
function handle401(res) {
  if (res.status === 401 && !_redirecting401) {
    _redirecting401 = true;
    // 使用 setTimeout 避免在 fetch 回调中同步跳转
    setTimeout(() => {
      window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }, 0);
  }
}

export function getCsrfToken() {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export function jsonHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCsrfToken(),
    'Accept': 'application/json',
  };
}

export function extractError(payload) {
  if (!payload) return '请求失败';
  if (payload.detail) return payload.detail;
  if (payload.error) return payload.error;
  if (payload.message) return payload.message;
  if (typeof payload === 'string') return payload;
  if (typeof payload === 'object') {
    const first = Object.values(payload)[0];
    if (Array.isArray(first)) return first[0];
    return first || '操作失败';
  }
  return '操作失败';
}

/**
 * 解析限流等待秒数。
 * 优先取 Retry-After 响应头；兜底从 DRF 默认文案
 * 「... Expected available in 2774 seconds.」中提取数字。
 */
function parseThrottleWait(res, payload) {
  if (res.headers && res.headers.get) {
    const ra = res.headers.get('Retry-After');
    if (ra && /^\d+$/.test(ra.trim())) return parseInt(ra.trim(), 10);
  }
  const text = (payload && (payload.detail || payload.error)) || '';
  const m = String(text).match(/(\d+)\s*seconds?/i);
  if (m) return parseInt(m[1], 10);
  return null;
}

/**
 * 将后端错误统一包装为带状态码的 Error。
 * 针对 429 限流：解析等待秒数，转换为「请求过于频繁，请稍后约 X 分钟再试」友好文案；
 * 若后端已返回友好文案（如自定义 1 分钟冷却提示），则保留原文。
 * err.wait 在能解析出等待时长时存在，供前端进入冷却倒计时。
 */
export function buildApiError(res, payload) {
  if (res.status === 429) {
    const wait = parseThrottleWait(res, payload);
    if (wait != null) {
      const msg = wait < 60
        ? `请求过于频繁，请稍后约 ${wait} 秒再试`
        : `请求过于频繁，请稍后约 ${Math.ceil(wait / 60)} 分钟再试`;
      const err = new Error(msg);
      err.status = 429;
      err.wait = wait;
      return err;
    }
    const err = new Error(extractError(payload));
    err.status = 429;
    return err;
  }
  const err = new Error(extractError(payload));
  err.status = res.status;
  return err;
}

export async function apiGet(url) {
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
  handle401(res);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw buildApiError(res, err);
  }
  return res.json();
}

export async function apiPost(url, data, isForm = false) {
  const opts = isForm
    ? { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() }, body: data }
    : { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) };
  const res = await fetch(url, opts);
  handle401(res);
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) throw buildApiError(res, payload);
  return payload;
}

export async function apiPatch(url, data) {
  const res = await fetch(url, { method: 'PATCH', headers: jsonHeaders(), body: JSON.stringify(data) });
  handle401(res);
  const payload = await res.json().catch(() => ({}));
  if (!res.ok) throw buildApiError(res, payload);
  return payload;
}

export async function apiDelete(url) {
  const res = await fetch(url, { method: 'DELETE', headers: { 'X-CSRFToken': getCsrfToken() } });
  handle401(res);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw buildApiError(res, err);
  }
  return true;
}

/**
 * 下载文件（Blob）
 * 用于文章导出等场景
 */
export async function apiDownloadFile(url) {
  const res = await fetch(url, { headers: { 'Accept': '*/*' } });
  handle401(res);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw buildApiError(res, err);
  }
  const disposition = res.headers.get('Content-Disposition') || '';
  let filename = 'download';
  const utf8Match = disposition.match(/filename\*=UTF-8''(.+)/i);
  if (utf8Match) {
    filename = decodeURIComponent(utf8Match[1]);
  } else {
    const basicMatch = disposition.match(/filename="?([^";]+)"?/);
    if (basicMatch) filename = basicMatch[1];
  }
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
}
