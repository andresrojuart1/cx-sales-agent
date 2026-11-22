#!/usr/bin/env python3
"""Parche Nova Domain Routing v11.5 -> v11.6 (puntos 2 y 5).
Uso: python3 apply_nova_patch.py workflow.json workflow_patched.json
Cada cambio busca un texto exacto una sola vez; si algo no coincide, aborta sin escribir nada.

(2) 4o intento de escritura con valores provisionales de cliente (POR IDENTIFICAR / Colombia)
    antes de marcar nova_routing_failed.
(5) Contador de intentos (nova_try_1..3) para tickets sin decision del agente (ya no se reintentan
    sin fin; al 3o se marca nova_routing_failed) y los tickets NUEVOS se procesan del mas viejo al mas nuevo.
La alerta de Slack no se toca: sigue llegando donde llega hoy.
"""
import json, sys, copy, uuid

src, dst = sys.argv[1], sys.argv[2]
wf = json.load(open(src))
nodes = {n["name"]: n for n in wf["nodes"]}
conn = wf["connections"]

def replace_once(text, old, new, where):
    assert text.count(old) == 1, f"[{where}] ancla no encontrada exactamente 1 vez ({text.count(old)}): {old[:70]!r}"
    return text.replace(old, new)

# ---- (5a) Filter & Prioritize: nuevos del mas viejo al mas nuevo + tope de intentos ----
f = nodes["Filter & Prioritize"]
js = f["parameters"]["jsCode"]
js = replace_once(js,
    "const fresh = [...res('new_ws'), ...res('new_cs')]\n  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));",
    "const fresh = [...res('new_ws'), ...res('new_cs')]\n  .sort((a, b) => new Date(a.created_at) - new Date(b.created_at)); // v11.6: oldest first (no starvation)",
    "Filter")
js = replace_once(js,
    "if (tg.includes('nova_routing_failed')) continue; // both writes failed before — a human handles it",
    "if (tg.includes('nova_routing_failed')) continue; // both writes failed before — a human handles it\n  if (tg.filter(x => /^nova_try_/.test(x)).length >= 3) continue; // v11.6: 3 attempts without a decision",
    "Filter")
f["parameters"]["jsCode"] = js

# ---- (2) Build Zendesk Update: payload con valores provisionales ----
b = nodes["Build Zendesk Update"]
exp = b["parameters"]["jsonOutput"]
exp = replace_once(exp,
    "if (grp) f.group_id = CS;",
    "if (grp) f.group_id = CS;\n"
    "  // v11.6: 4th attempt — required client fields as placeholders (Zendesk rejects client tickets without them)\n"
    "  const PH = [{ id: 25216274102548, value: 'POR IDENTIFICAR' }, { id: 44459532208276, value: 'POR IDENTIFICAR' }, { id: 33369429616276, value: 'colombia_client_country' }];\n"
    "  const p = { ...own, comment: { public: false, body: body + '\\n(Required client fields were filled with POR IDENTIFICAR / Colombia as placeholders so the ticket could be assigned. Please correct them once the client is identified.)' }, custom_fields: cf.concat([{ id: PAYFLOW, value: 'n/a' }], PH) };\n"
    "  if (grp || Number(tk.group_id) === CS) p.group_id = CS;",
    "Build Zendesk Update")
exp = replace_once(exp,
    "fallback: { ticket: f },",
    "fallback: { ticket: f }, placeholder: { ticket: p },",
    "Build Zendesk Update")
b["parameters"]["jsonOutput"] = exp

# ---- (2) nodo nuevo: Retry 3 (Client placeholders) ----
base = nodes["Fallback: Assign Owner Only"]
new_retry = copy.deepcopy(base)
new_retry["id"] = str(uuid.uuid4())
new_retry["name"] = "Retry 3 (Client placeholders)"
new_retry["parameters"]["jsonBody"] = "={{ JSON.stringify($('Build Zendesk Update').item.json.placeholder) }}"
new_retry["position"] = [base["position"][0] + 224, base["position"][1] + 160]
wf["nodes"].append(new_retry)
# Fallback (error) -> Retry 3 ; Retry 3 ok -> Mark Write: Updated ; Retry 3 error -> Tag Routing Failed
fb = conn["Fallback: Assign Owner Only"]["main"]
assert fb[1][0]["node"] == "Tag Routing Failed", "estructura inesperada en Fallback"
fb[1] = [{"node": "Retry 3 (Client placeholders)", "type": "main", "index": 0}]
conn["Retry 3 (Client placeholders)"] = {"main": [
    [{"node": "Mark Write: Updated", "type": "main", "index": 0}],
    [{"node": "Tag Routing Failed", "type": "main", "index": 0}]]}

# ---- (5b) contador de intentos en la rama "sin decision" ----
hd = conn["Has Decision?"]["main"]
assert hd[1][0]["node"] == "Loop Over Tickets", "estructura inesperada en Has Decision?"
set_node = {
  "parameters": {"mode": "raw", "options": {},
    "jsonOutput": "={{ (() => { const tk = $('Loop Over Tickets').item.json || {}; const n = (tk.tags || []).filter(x => /^nova_try_/.test(x)).length + 1; return JSON.stringify({ ticket_id: tk.ticket_id, tags: n >= 3 ? ['nova_try_' + n, 'nova_routing_failed'] : ['nova_try_' + n] }); })() }}"},
  "type": "n8n-nodes-base.set", "typeVersion": 3.4, "id": str(uuid.uuid4()),
  "name": "Next Attempt Tag", "position": [59664, 19392]}
tag_node = copy.deepcopy(nodes["Add Routing Tags"])
tag_node["id"] = str(uuid.uuid4()); tag_node["name"] = "Add Attempt Tag"
tag_node["parameters"]["url"] = "=https://getontop.zendesk.com/api/v2/tickets/{{ $json.ticket_id }}/tags.json"
tag_node["parameters"]["jsonBody"] = "={{ JSON.stringify({ tags: $json.tags }) }}"
tag_node["position"] = [59904, 19552]
wf["nodes"] += [set_node, tag_node]
hd[1] = [{"node": "Next Attempt Tag", "type": "main", "index": 0}]
conn["Next Attempt Tag"] = {"main": [[{"node": "Add Attempt Tag", "type": "main", "index": 0}]]}
conn["Add Attempt Tag"] = {"main": [[{"node": "Loop Over Tickets", "type": "main", "index": 0}]]}

# nota de version (texto informativo)
ov = nodes["Note · Overview"]["parameters"]["content"]
nodes["Note · Overview"]["parameters"]["content"] = ov.replace("## 🤖 Nova · Domain routing agent v11.5 (every 5 min)", "## 🤖 Nova · Domain routing agent v11.6 (every 5 min)", 1) + "\n\n**v11.6:** 4th write attempt with client placeholders (POR IDENTIFICAR / Colombia) before `nova_routing_failed`; new tickets processed oldest-first; tickets without an agent decision get `nova_try_N` and stop after 3."

json.dump(wf, open(dst, "w"), ensure_ascii=False, indent=2)
print("OK ->", dst, "| nodos:", len(wf["nodes"]))
