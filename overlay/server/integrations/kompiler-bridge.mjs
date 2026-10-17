/** Strict local-only HTTP integration with Kompiler API 1.0/1.1 (verified against 0.8.0-alpha.1).
 * No command execution, semantic rewriting, cache sharing or state publication.
 */
import { fail } from '../errors.mjs';

export function safeKompilerEndpoint(env = process.env) {
  const raw = env.KONSTELLATION_KOMPILER_URL;
  if (!raw) return null;
  let u;
  try { u = new URL(raw); } catch { fail('INVALID_CONFIG', 'Invalid Kompiler URL.', 500); }
  if (u.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(u.hostname)
      || u.username || u.password || u.search || u.hash || (u.pathname !== '/' && u.pathname !== '')) {
    fail('INVALID_CONFIG', 'Kompiler must use local loopback HTTP without URL path or credentials.', 500);
  }
  return u.origin;
}

export class KompilerBridge {
  constructor({ url = safeKompilerEndpoint(), token = process.env.KONSTELLATION_KOMPILER_TOKEN || '',
    fetcher = fetch, timeoutMs = 8500, maxBytes = 2_000_000 } = {}) {
    // Injected URLs must obey the same loopback rule as configured endpoints.
    this.url = url == null ? null : safeKompilerEndpoint({KONSTELLATION_KOMPILER_URL:url});
    this.token = token;
    this.fetcher = fetcher;
    this.timeoutMs = timeoutMs;
    this.maxBytes = maxBytes;
  }
  async request(method, endpoint, data) {
    if (!this.url) fail('UPSTREAM_UNAVAILABLE', 'Kompiler is not configured.', 503);
    const allowed = {
      'GET /v1/capabilities': true,
      'POST /v1/queries/validate': true,
      'POST /v1/runs': true,
      'POST /v1/projections/v6': true,
    };
    if (!allowed[`${method} ${endpoint}`]) fail('ACCESS_DENIED', 'Kompiler operation is not allowed.', 403);
    const headers = { Accept: 'application/json' };
    if (data !== undefined) headers['Content-Type'] = 'application/json';
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    let response;
    try {
      response = await this.fetcher(this.url + endpoint, {
        method, headers, redirect: 'error', signal: AbortSignal.timeout(this.timeoutMs),
        ...(data === undefined ? {} : { body: JSON.stringify(data) }),
      });
    } catch {
      fail('UPSTREAM_UNAVAILABLE', 'Kompiler is unreachable or timed out.', 502);
    }
    if (!response.headers.get('content-type')?.toLowerCase().includes('application/json'))
      fail('UPSTREAM_INVALID', 'Kompiler response is not JSON.', 502);
    const length = Number(response.headers.get('content-length') || 0);
    if (length > this.maxBytes) fail('UPSTREAM_LIMIT', 'Kompiler response exceeds the byte limit.', 502);
    // Stream with a strict byte bound even if content-length is omitted/untrusted.
    const reader = response.body?.getReader();
    if (!reader) fail('UPSTREAM_INVALID', 'Empty Kompiler response.', 502);
    const pieces = []; let used = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        used += value.byteLength;
        if (used > this.maxBytes) { await reader.cancel(); fail('UPSTREAM_LIMIT', 'Kompiler response exceeds the byte limit.', 502); }
        pieces.push(value);
      }
    } finally { reader.releaseLock(); }
    let json;
    try { json = JSON.parse(new TextDecoder().decode(Buffer.concat(pieces))); }
    catch { fail('UPSTREAM_INVALID', 'Kompiler returned invalid JSON.', 502); }
    if (!response.ok) fail('UPSTREAM_ERROR', `Kompiler rejected the operation (HTTP ${response.status}).`, response.status === 401 || response.status === 403 ? 502 : 422,
      { upstreamCode: String(json?.code || json?.error?.code || 'UNKNOWN').slice(0, 80) });
    return json;
  }
  async capabilities() {
    const data = await this.request('GET', '/v1/capabilities');
    if (data?.protocol !== 'kompiler.capabilities' || !['1.0','1.1'].includes(data.version)
        || !Array.isArray(data.targets) || data.targets.some(t => !t || typeof t.target_id !== 'string' || !t.target_id))
      fail('UPSTREAM_INVALID', 'Unrecognized Kompiler capabilities protocol or target identifiers.', 502);
    return data;
  }
  async validate(plan) {
    const data = await this.request('POST', '/v1/queries/validate', plan);
    if (typeof data?.valid !== 'boolean') fail('UPSTREAM_INVALID', 'Invalid Kompiler validation response.', 502);
    return data;
  }
  async run(plan) {
    const data = await this.request('POST', '/v1/runs', plan);
    if (data?.protocol !== 'kompiler.context-pack' || !['1.0','1.1'].includes(data.version)
        || typeof data.context_pack_id !== 'string' || !data.context_pack_id
        || !Array.isArray(data.records) || !data.execution || typeof data.execution !== 'object')
      fail('UPSTREAM_INVALID', 'Unrecognized or incomplete Kompiler Context Pack.', 502);
    return data;
  }
  async projection(pack, surfaceId) {
    if (pack?.protocol !== 'kompiler.context-pack' || !['1.0','1.1'].includes(pack.version))
      fail('INVALID_QUERY', 'Projection requires a compatible derived Context Pack.', 422);
    const state = await this.request('POST', '/v1/projections/v6', {
      context_pack: pack, ...(surfaceId ? { surface_id: surfaceId } : {}), recipe_id: 'recipe:konstellation-bridge',
    });
    if (state?.schema_version !== '6.0' || state?.artifact_type !== 'kristal_state'
        || !Array.isArray(state.assertions) || !Array.isArray(state.provenance))
      fail('UPSTREAM_INVALID', 'Projection is not a compatible derived v6 state.', 502);
    return state;
  }
}
