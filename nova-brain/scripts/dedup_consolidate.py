"""Consolidar duplicados de WS SIN merge (workflows.md §K y §L). Dry-run por defecto.
  python3 -I dedup_consolidate.py                      # simula: grupos, qué se haría, riesgos
  python3 -I dedup_consolidate.py --apply              # ejecuta (SOLO con OK explícito de Mike)
Opciones: --skip 260148,260177   tickets a excluir
          --agent-replied ids    viejos donde un AGENTE HUMANO ya respondió (se saltan si el worker escribió después)
Detección: mismo nombre completo (>=2 palabras) en el asunto "Conversation with NOMBRE" (new/open de WS).
Antes de --apply: mostrar a Mike el borrador y la lista de grupos."""
import os, sys, re, json, time, datetime, argparse, collections, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zd import (search_export, show_many, users, put, get, nova_note, category_labels, add_tags, csat_score,
                CX_TEAM, UKRAINE, WS, ST_OPEN)
import sunco

ST_SOLVED = 22614180871444
TAGS = ["dup_cerrado_nova", "24_hours_tickets"]
TYPE_OF_REQUEST = [{"id": 32273934250132, "value": "issue_request"}]   # decisión de Mike para duplicados
CATF = 22865771347348
P = lambda s: datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--skip", default="")
ap.add_argument("--agent-replied", default="")
a = ap.parse_args()
SKIP = {int(x) for x in a.skip.split(",") if x}
AGENT = {int(x) for x in a.agent_replied.split(",") if x}


def norm(subject):
    m = re.search(r"conversation with\s+(.*)$", subject or "", re.I)
    s = unicodedata.normalize("NFKD", (m.group(1) if m else "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


T = search_export(f"type:ticket group:{WS} status:new status:open")
by = collections.defaultdict(list)
for t in T:
    n = norm(t.get("subject"))
    if len(n.split()) >= 2 and not n.startswith("user "):
        by[n].append(t["id"])
groups = [sorted(v) for v in by.values() if len(v) > 1]
live = {t["id"]: t for t in show_many([i for g in groups for i in g])}
cats = category_labels()
names = users(t["assignee_id"] for t in live.values())


def cat(t):
    for f in t.get("custom_fields", []):
        if f["id"] == CATF and f["value"]:
            return cats.get(f["value"], f["value"])
    return "(sin categoría)"


def lang_of(conv):
    try:
        txt = " ".join(m["content"].get("text", "") for m in sunco.messages(conv) if m["author"]["type"] == "user").lower()
    except Exception:
        return "es"
    pt = len(re.findall(r"\b(você|voce|obrigad[oa]|olá|não|nao|preciso|meu|minha)\b", txt))
    en = len(re.findall(r"\b(the|my|i|is|not|have|hello|hi|please|account|money|transfer|why|need)\b", txt))
    es = len(re.findall(r"\b(el|la|mi|que|no|hola|cuenta|dinero|gracias|necesito|por|con|me|una)\b", txt))
    return "pt" if pt > max(en, es) else ("en" if en > es else "es")


def text(lang, new, olds):
    pl = len(olds) > 1
    ol = ", ".join(f"#{o}" for o in olds)
    if lang == "en":
        return (f"Hi, we noticed you have opened several conversations about the same topic. To help you better, we'll keep working on your case in this conversation (ticket #{new}) and we'll close the previous {'ones' if pl else 'one'} ({ol}). We'll reply to you here during the day. Thanks for your patience.")
    if lang == "pt":
        return (f"Olá, vimos que você abriu várias conversas sobre o mesmo assunto. Para atendê-lo melhor, vamos continuar trabalhando no seu caso nesta conversa (ticket #{new}) e vamos encerrar {'as anteriores' if pl else 'a anterior'} ({ol}). Responderemos por aqui ao longo do dia. Obrigado pela sua paciência.")
    return (f"Hola, vemos que has abierto varias conversaciones por el mismo tema. Para atenderte mejor, vamos a seguir trabajando tu caso en esta conversación (ticket #{new}) y cerraremos {'las anteriores' if pl else 'la anterior'} ({ol}). En el transcurso del día te responderemos por aquí. Gracias por tu paciencia.")


def old_detail(i):
    t = live[i]
    lines = [f"— Ticket viejo #{i} · creado {t['created_at'][:16].replace('T', ' ')} UTC · estado {t['status']} · categoría {cat(t)} · asignado: {names.get(t['assignee_id'], '(sin dueño)')}"]
    nv = nova_note(i)
    if nv:
        lines.append("  Nota Nova: " + " | ".join(f"{k}: {v[:250]}" for k, v in nv.items()))
    try:
        for m in sunco.messages(sunco.conversation_id(i))[-8:]:
            c = m["content"]
            lines.append(f"  [{m['received'][:16]}] {'worker' if m['author']['type'] == 'user' else 'agente/bot'}: {(c.get('text') or c['type']).replace(chr(10), ' ')[:260]}")
    except Exception:
        lines.append("  (no se pudo leer la conversación)")
    return "\n".join(lines)


def plan_group(g):
    g = [i for i in g if i not in SKIP and i not in UKRAINE]
    if len(g) < 2:
        return None
    cur = {t["id"]: t for t in show_many(g)}
    keep = max(g, key=lambda i: (cur[i]["created_at"], i))
    res = {"keep": keep, "olds": [], "skipped": []}
    if cur[keep]["status"] not in ("new", "open"):
        res["skipped"].append((keep, "el reciente ya no está new/open"))
        return res
    for o in (i for i in g if i != keep):
        if cur[o]["status"] not in ("new", "open"):
            res["skipped"].append((o, "ya no new/open")); continue
        if o in AGENT:
            try:
                ms = sunco.messages(sunco.conversation_id(o))
                biz = [P(m["received"]) for m in ms if m["author"]["type"] == "business"]
                if biz and any(P(m["received"]) > biz[-1] for m in ms if m["author"]["type"] == "user"):
                    res["skipped"].append((o, "conversación activa tras respuesta de agente: avisar a Mike")); continue
            except Exception:
                pass
        res["olds"].append(o)
    other = [live[o]["assignee_id"] for o in res["olds"] if live[o]["assignee_id"] and live[o]["assignee_id"] not in CX_TEAM]
    res["other_area"] = other[0] if other and (not cur[keep]["assignee_id"] or cur[keep]["assignee_id"] in CX_TEAM) else None
    return res


def close_old(o, keep):
    """§L: etiquetas ANTES, verificadas; luego solve; devuelve (ok, motivo)."""
    if not add_tags(o, TAGS):
        return False, "etiquetas no quedaron: NO se resolvió"
    r = put(f"/tickets/{o}.json", {"ticket": {
        "comment": {"public": False, "body": f"🤖 Nova · Duplicado de #{keep}. El worker fue avisado en #{keep} y el detalle de este ticket quedó en nota interna allá. Cerrado sin merge (aprobado por Mike)."},
        "custom_status_id": ST_SOLVED, "custom_fields": TYPE_OF_REQUEST}})
    if r.status_code != 200:
        d = (r.json().get("details", {}).get("base") or [{}])[0].get("description", r.text[:120]) if r.text else r.status_code
        return False, f"{r.status_code}: {d}"
    return True, ""


def apply_group(res):
    keep, olds = res["keep"], res["olds"]
    body = "🤖 Nova · Duplicados consolidados en este ticket (sin merge). Detalle de los tickets anteriores:\n\n" + "\n\n".join(old_detail(o) for o in olds) + "\n\nAcción: se avisó al worker que seguimos aquí y se cerraron los anteriores. (aprobado por Mike)"
    fields = {"assignee_id": res["other_area"], "group_id": WS, "custom_status_id": ST_OPEN} if res["other_area"] else {}
    if put(f"/tickets/{keep}.json", {"ticket": {"comment": {"public": False, "body": body}, **fields}}).status_code != 200:
        return {"error": "nota falló, no se avisó ni cerró nada"}
    if fields and get(f"/tickets/{keep}.json")["ticket"]["group_id"] != WS:
        put(f"/tickets/{keep}.json", {"ticket": {"group_id": WS}})
    conv = sunco.conversation_id(keep)
    if not conv:
        return {"error": "sin conversation_id: no se avisó, no se cerró nada"}
    mode, st = sunco.smart_send(keep, text(lang_of(conv), keep, olds), "es")
    if mode != "text" or st not in (200, 201):
        return {"error": f"envío {mode}/{st}: viejos NO cerrados"}
    return {"sent": True, "closed": [(o, *close_old(o, keep)) for o in olds]}


plans = [p for p in (plan_group(g) for g in groups) if p]
n_old = sum(len(p["olds"]) for p in plans)
print(f"Grupos: {len(plans)} | viejos a cerrar: {n_old} | mensajes: {sum(1 for p in plans if p['olds'])}")
print("A otra área:", [(p["keep"], names.get(p["other_area"], p["other_area"])) for p in plans if p.get("other_area")])
print("Saltados:", [(p["keep"], p["skipped"]) for p in plans if p["skipped"]])
if not a.apply:
    for p in plans:
        if p["olds"]:
            print(f"  mantener #{p['keep']} ← cerrar {' '.join('#' + str(o) for o in p['olds'])}")
    print("\nDRY-RUN: no se envió ni modificó nada. Usa --apply solo con OK de Mike.")
    sys.exit()

todo = [p for p in plans if p["olds"]]
log = []
for k, p in enumerate(todo):
    r = apply_group(p)
    log.append({**p, **r})
    if k == 0:   # CANARIO: verificar TODO antes de seguir
        time.sleep(35)
        bad = []
        for o, ok, why in r.get("closed", []):
            t = get(f"/tickets/{o}.json")["ticket"]
            if not ok: bad.append(f"#{o} no cerró: {why}")
            elif t["status"] != "solved" or not set(TAGS) <= set(t["tags"]) or csat_score(o) != "unoffered":
                bad.append(f"#{o} status={t['status']} tags_ok={set(TAGS) <= set(t['tags'])} csat={csat_score(o)}")
        if r.get("error") or bad or not r.get("closed"):
            print("DETENIDO tras el canario:", r.get("error") or bad or "nada cerrado"); break
        print("Canario OK, sigo…")
print("Resultado:", json.dumps([{k: v for k, v in x.items() if k in ("keep", "closed", "error")} for x in log], default=str)[:3000])
