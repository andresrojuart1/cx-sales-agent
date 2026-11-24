"""Foto de la cola de soporte (solo lectura). python3 -I queue_snapshot.py"""
import os, sys, datetime, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zd import count, search_export, users, WS, CS, ST_IR, CX_TEAM

today = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)).date()
yday = today - datetime.timedelta(days=1)
q = {
    "Abiertos WS": f"type:ticket group:{WS} status:new status:open",
    "Abiertos CS": f"type:ticket group:{CS} status:new status:open",
    "Internally raised": f"type:ticket custom_status_id:{ST_IR}",
    "Pending WS": f"type:ticket group:{WS} status:pending",
    "Sin dueño WS": f"type:ticket group:{WS} status<solved assignee:none",
    "Entraron hoy WS": f"type:ticket group:{WS} created>={today}",
    "Entraron ayer WS": f"type:ticket group:{WS} created>={yday} created<{today}",
    "Resueltos ayer WS": f"type:ticket group:{WS} solved>={yday} solved<{today}",
}
with ThreadPoolExecutor(6) as ex:
    R = dict(zip(q, ex.map(count, q.values())))
for k, v in R.items():
    print(f"{k}: {v}")
tot = R["Abiertos WS"] + R["Abiertos CS"] + R["Internally raised"]
print(f"TOTAL PILOTO: {tot} (meta 50, sobran {tot - 50})")

T = search_export(f"type:ticket group:{WS} status<solved")
names = users(t["assignee_id"] for t in T)
by = collections.defaultdict(collections.Counter); ids = {}
for t in T:
    st = "IR" if t.get("custom_status_id") == ST_IR else t["status"]
    who = names.get(t["assignee_id"], "(sin dueño)"); ids[who] = t["assignee_id"]
    by[who][st] += 1
print("\nPor persona (WS sin resolver):")
for w, c in sorted(by.items(), key=lambda x: -sum(x[1].values())):
    tag = "" if ids.get(w) in CX_TEAM or ids.get(w) is None else "  [otra área]"
    print(f"  {sum(c.values()):4} {w}: " + ", ".join(f"{k}={v}" for k, v in c.items()) + tag)
old = sorted([t for t in T if t["status"] in ("new", "open")], key=lambda t: t["created_at"])[:5]
print("\nMás viejos abiertos:", ", ".join(f"#{t['id']} ({t['created_at'][:10]}, {names.get(t['assignee_id'], 'sin dueño')})" for t in old))
