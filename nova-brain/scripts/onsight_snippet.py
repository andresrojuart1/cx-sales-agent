# Pegar como source_code de mcp__Ada_Aura__run_code_tool
#   code_tool_id = "6ab853b4edbc966686882620", inputs = {"email": "", "question": ""}
# El sandbox de Ada tiene ONSIGHT_TOKEN en el entorno y la función fetch().
# Límite: 10 requests por corrida (initialize + notified = 2, así que caben 8 consultas).
# Cambia QUERIES; el resultado son las filas completas (structuredContent).
import json, os
URL = "https://mcp.onsight.getontop.com/mcp"; CID = "0ef9e62e-cb8e-4f3f-a3fc-1ba33f25d301"
H = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
     "Authorization": "Bearer " + os.getenv("ONSIGHT_TOKEN", "")}
def pb(b):
    t = b.strip()
    if t.startswith("{"): return json.loads(t)
    last = None
    for l in t.split("\n"):
        if l.startswith("data:") and l[5:].strip().startswith("{"): last = json.loads(l[5:].strip())
    return last
i = fetch("POST", URL, headers=H, body=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "nova", "version": "1"}}}))
for k in i["headers"]:
    if str(k).lower() == "mcp-session-id": H["MCP-Session-Id"] = i["headers"][k]
fetch("POST", URL, headers=H, body=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
def sql(q, n=50):
    r = fetch("POST", URL, headers=H, timeout=30, body=json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
              "params": {"name": "onsight_execute_sql", "arguments": {"connector_id": CID, "sql": q, "max_rows": n}}}))
    res = pb(r["body"]).get("result", {}); sc = res.get("structuredContent")
    return {"cols": sc.get("columns"), "rows": sc.get("rows")} if sc else [c.get("text", "")[:3000] for c in res.get("content", [])]
QUERIES = {
    "contractor": "select cod_contractor, des_email, des_kyc_check_status, des_wallet_status from process_data.contractor where lower(des_email)='x@y.com'",
}
{k: sql(v) for k, v in QUERIES.items()}
