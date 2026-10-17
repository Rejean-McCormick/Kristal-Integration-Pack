<script>
  import { onMount } from 'svelte';
  export let authToken = '';
  let connected = false, capabilities = null, query = '', busy = false, error = '', result = null, projection = null, surfaceId = '';
  const headers = () => ({ 'Content-Type': 'application/json', ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}) });
  async function api(endpoint, payload, method = 'POST') {
    const r = await fetch(`/api/kompiler/${endpoint}`, { method, headers: headers(), ...(method === 'GET' ? {} : { body: JSON.stringify(payload) }) });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error?.message || `HTTP error ${r.status}`);
    return data;
  }
  onMount(async () => {
    try {
      capabilities = await api('capabilities', undefined, 'GET'); connected = true;
      const target = capabilities.targets?.[0];
      const operation = target?.operations?.find((x) => !x.semantics?.requires_surface) || target?.operations?.[0];
      if (target && operation) query = JSON.stringify({version:'1.1',request_id:'konstellation-ui',
        topic:'exploration',operations:[{id:'read',target:target.target_id,operation:operation.operation_id,params:{}}]},null,2);
    } catch { connected = false; }
  });
  async function execute(validateOnly) {
    busy = true; error = ''; result = null; projection = null;
    try {
      const plan = JSON.parse(query);
      result = await api(validateOnly ? 'validate' : 'run', plan);
    } catch(e) { error = e?.message || 'Invalid query'; }
    finally { busy = false; }
  }
  async function project() {
    if (!result) return;
    busy = true; error = '';
    try { projection = await api('projection', {context_pack:result, ...(surfaceId ? {surface_id:surfaceId}:{})}); }
    catch(e) { error = e?.message || 'Projection unavailable'; }
    finally { busy = false; }
  }
  function download(data, filename) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)], {type:'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
</script>

{#if connected}
  <details class="kompiler-panel">
    <summary>◈ Kompiler — read-only Kristal queries</summary>
    <div class="kompiler-content">
      <p>Queries run through Kompiler. Results are derived reading views, not domain authority.</p>
      <label for="kompiler-query">Query plan (kompiler.query/1.1)</label>
      <textarea id="kompiler-query" bind:value={query} rows="9" spellcheck="false"></textarea>
      <div class="kompiler-actions">
        <button disabled={busy} on:click={() => execute(true)}>Validate</button>
        <button disabled={busy} on:click={() => execute(false)}>Run</button>
      </div>
      {#if error}<p role="alert">{error}</p>{/if}
      {#if result}
        <p role="status">{result.protocol || 'Result'} · {result.context_pack_id || result.request_id || 'without a pack identifier'}</p>
        <p>Records : {result.records?.length ?? '—'} · Sources : {result.sources?.length ?? '—'}</p>
        <div class="kompiler-actions">
          <button on:click={() => download(result,'context-pack.json')}>Export Context Pack JSON</button>
          {#if result.context_pack_id}
            <label for="kompiler-surface">Surface ID (optional)</label>
            <input id="kompiler-surface" bind:value={surfaceId} placeholder="Auto for a single surface" />
            <button disabled={busy} on:click={project}>Project v6</button>
          {/if}
        </div>
        {#if projection}
          <p>Derived projection. It does not replace the source state snapshot.</p>
          <button on:click={() => download(projection,'kristal-projection-v6.json')}>Export v6 projection</button>
        {/if}
        <details><summary>Inspect JSON (provenance, coverage, status)</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
      {/if}
    </div>
  </details>
{/if}
<style>
  .kompiler-panel { margin:1.25rem 0; border:1px solid #aaa7; border-radius:10px; padding:1rem; }
  .kompiler-panel summary {cursor:pointer;font-weight:650}
  .kompiler-content {display:grid;gap:.7rem;margin-top:1rem}
  textarea {width:100%;font-family:ui-monospace,monospace;min-height:9rem;border:1px solid #aaa;border-radius:6px;padding:.65rem;background:var(--surface,#fff);color:var(--text,#222)}
  .kompiler-actions {display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}
  .kompiler-actions button,button {padding:.45rem .7rem;border:1px solid #999;border-radius:5px;cursor:pointer}
  pre {white-space:pre-wrap;overflow-wrap:anywhere;max-height:22rem;overflow:auto;font-size:.75rem}
</style>
