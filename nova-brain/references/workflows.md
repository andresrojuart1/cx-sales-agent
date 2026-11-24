# Flujos de trabajo de Nova

## A. Revisar la cola
`python3 -I scripts/queue_snapshot.py` → imprime: abiertos WS/CS, Internally Raised, pending WS, sin dueño, carga por persona (open/pending/IR), entrantes hoy vs. ayer, 5 más viejos. Entregar:
- Total piloto = abiertos WS + CS + IR (meta ≤ 50) y distancia a la meta.
- Tabla por persona y 1–3 acciones concretas.
Para "otras áreas": tickets de WS asignados a alguien que no es del equipo CX.

## A2. Triage de la cola completa ("qué se resuelve fácil y qué está duplicado")
**Script:** `python3 -I scripts/triage_queue.py --out <ruta>/ws_triage.json` hace los pasos 1–4 (solo lectura) e imprime el reporte con IDs; luego agrupa y reporta. Los pasos de abajo explican qué hace y por qué.
1. `zd.search_export("type:ticket group:WS status:new status:open")` (hoy ~310; la cola cambia mientras trabajas).
2. **El contenido real de mensajería NO está en los comentarios de Zendesk** (solo "Conversation with NOMBRE" y notas del sistema): leer el último mensaje del usuario por Sunshine (`sunco.conversation_id` + `sunco.messages`, autor `user`). Hacerlo en Python con ThreadPoolExecutor(12), sin volcar transcripts al contexto.
3. Clasificar por regex sobre ese texto (token/bloqueo, contraseña/OTP, transferencia pendiente/rechazada, tarjeta, KYC, PA, certificado, eliminar cuenta…). Ojo: ~40 % cae en "Otro/general" y muchos son "asesor / ¿cuándo me atienden?" tras un handoff de Ada: son de primer toque humano, no de área.
4. Reportar en 3 bloques: **CX fácil** (token, contraseña, certificado, PA/Boost, eliminar cuenta) · **va a un área** (Payouts/Card Ops/Compliance/Tech/Account Mgmt, ver §B) · **duplicados** (ver §K). Con IDs.
5. Causas raíz a mencionar: auto-merge de identidades fallando ("Unsuccessful Merge into Another User Identification" en notas internas) → un requester nuevo por conversación → duplicados; y exceso de handoffs de Ada sin resolver.

## B. Revisar los tickets de una persona o un lote
1. `zd.search_export("type:ticket group:WS status<solved assignee:<id>")`.
2. Para cada ticket, leer la última nota interna "🤖 Nova · Domain routing + diagnosis" (campos `• Ask:`, `• Onsight:`, `• Suggested action:`). Si no hay nota, usar la categoría.
3. Para mensajería, si importa el último mensaje del usuario: `sunco.py last <ticket>`.
4. Agrupar por **causa raíz**, no solo por categoría: un incidente (p. ej. 30 tickets de token en 2 h) se maneja con un mensaje masivo, no caso por caso.
5. Entregar tabla: tema · tickets · qué hacer (CX resuelve / área / incidente / Bre-B bulk).

Lo que **CX resuelve** (Mike lo confirmó): desbloqueo de cuentas, contraseñas bloqueadas, eliminación de cuenta (runbook *DeleteAccount* en Hoops), duplicados, certificados/extractos, preguntas de Paycheck Advance y Boost cubiertas por el knowledge de Aura.
Lo que **va a áreas**: errores técnicos de transferencia, face match con KYC verificado, cambio de ID/Tax ID → Tech (Lucho); KYC/fraude → Compliance (Jorge); transferencias pendientes/devueltas/recall → Payouts (Camila); PA atascado/elegibilidad → Slenny; compras no reconocidas → Card Ops; el cliente no pagó → Account Management.

## C. Responder un ticket
- Mensajería → `sunco.py send <ticket> "<texto>"` (detecta conversación; si WhatsApp >24 h manda template y avisa).
- Correo/web/api → comentario público con `author_id` 26024622590356 (Ontop Support) salvo que Mike pida otra cosa.
- Luego: `custom_status_id` 25685916283028 (Waiting) + nota interna "🤖 Nova · <qué se respondió> (aprobado por Mike)".
- Si el usuario respondió solo "gracias", volver a Waiting sin escribir.
- Antes de escribir, comprobar que nadie respondió después del último mensaje del usuario (si Jaime u otro está activo, no cruzarse).

## D. Mensaje masivo por incidente
1. Identificar los tickets por causa/país con las notas de Nova.
2. Redactar ES + EN, sin proveedor ni ETA; mostrar a Mike; esperar OK.
3. Enviar con un subagente general (instrucciones cortas): Sunshine o comentario público, template si >24 h, Waiting + nota.
4. Reportar: enviados ES/EN, template, saltados (y por qué), fallidos.

## E. Certificados y extractos con Ada
Crear test case y correrlo (Ada MCP):
```
edit_agent_config(entity_type="test_case", operation="create", confirmed=true, fields={
  name: "OPS #<ticket> – certificado <CA> ...",
  user_message: "Hola, necesito mi certificado de servicios en español, sin la compensación mensual.",
  scenario_goal: "Eres un worker con sesión iniciada. Quieres tu Certificate of Services en <idioma> <con/sin> compensación. Si pregunta el contrato, eliges <CA>. Cuando lo genere, agradeces y terminas.",
  language: "es", channel_id: "bmF0aXZlLWNoYXQtNjg2NzNmN2JjZDA3ODA1YjI0NjRlYzJh",
  variables: [user_type=worker, b2b_or_b2c=B2C, user_email=<email>, contrato=<CA>],
  success_criteria: ["Aura genera el certificado ..."] })
edit_agent_config(entity_type="test_run", operation="create", confirmed=true, fields={test_case_ids:[...]})
get_test_runs(..., include_transcript=true)  → buscar el link n8n.tools.getontop.com/webhook/aura/v2/documents/download?... (vale 24 h; Aura también lo envía al correo registrado)
```
- Cuentas eliminadas: el correo queda como `XXX@GMAIL.COM-DELETED`.
- Contrato por tarea de Yousign o con documento propio del cliente (`is_own_document=1`): Aura no emite certificado → ofrecer el extracto.
- Extractos de wallet: mismo flujo pidiendo "extracto de mi Payroll Account de <fecha> a <fecha> en PDF".
- Bug conocido del generador: en contratos PAY PER TASK/TIME muestra `amt_monthly_compensation` (tarifa ×4, redondeada) en vez de la tarifa por hora. Mike mantiene el generador (workflow n8n `/aura/v2/documents`).
- Documentos a medida (p. ej. saldo a una fecha): calcular en Onsight y armar Excel con membrete de Ontop (encabezado morado #291960 "ontop", título, titular, fecha, saldo destacado, detalle, nota al pie). Mostrar a Mike antes de enviarlo.

## F. Onsight
Usar `scripts/onsight_snippet.py` como `source_code` de `mcp__Ada_Aura__run_code_tool` (code_tool_id 6ab853b4edbc966686882620, inputs {"email":"","question":""}). Máx. 10 requests por corrida: agrupar consultas con UNION ALL. Leer `structuredContent` para filas completas.

## G. Escalar a otra área
Asignar a la persona del área **en el grupo WS**, status Open, con nota interna en el formato del equipo:
```
<Tema> — <CR>

Hola <Nombre>, ¿me ayudas con este caso? Revisión de <persona de CX> (CX).

<Contexto: qué pide el worker, qué revisamos en CX, datos de Onsight>

¿Puedes confirmar?
1. ...
2. ...

Por favor responde directo al worker en este ticket (es WhatsApp: responder desde el Agent Workspace). ¡Gracias!
```

## H. Plan de fin de semana
- Lo que necesita otra área → mover a Internally Raised (31769974642836) con nota, sin side conversation, dejando a la persona del área como asignada.
- Aviso de demora (aprobado por Mike):
  - ES: "Hola, sabemos lo importante que es para ti recibir una respuesta a tiempo. Tu caso ya está en revisión con nuestro equipo y, como estamos entrando al fin de semana, nuestra respuesta puede tardar un poco más de lo habitual. Te escribiremos por este mismo medio apenas tengamos una actualización. Gracias por tu paciencia."
  - EN: "Hi, we know getting timely support matters to you. Your request is already being reviewed by our team and, as we head into the weekend, our response may take a little longer than usual. We'll follow up right here as soon as we have an update. Thanks for your patience."
- Lunes 6:00 a. m. COL: tarea programada que reabre en Open lo movido a IR durante el fin de semana.

## I. Aura (Ada)
- `edit_agent_behavior(operation="update", ...)` crea un changeset; mostrar el diff; `promote` pide preview → Mike confirma → `promote confirmed=true`.
- Custom instructions: máx. 300 caracteres y máx. 20 activas (para agregar una, apagar otra).
- Nunca cambiar Aura solo por algo de Slack: solo con lo publicado en el Help Center o por pedido explícito de Mike.

## J. Comisiones mensuales del equipo
Archivo modelo: "Comisiones Q3_1-30 Sept.xlsx" (Drive 1AyAZzuZj5DxctCU8yuEiwVyqXV3BszC5). Reglas (hoja Objectives): CSAT grupo ≥95% → 25 · FRT grupo ≤5 min → 20 · ART grupo ≤3 min → 15 · ACT grupo ≥90% → 10 · CSAT individual ≥95% → 25 · Productividad → 45 · Rockstar por equipo → 50 (50% CSAT/0.95 + 25% min(5/FRT,1) + 15% min(3/ART,1) + 10% min(ACT/0.9,1)). **Regla nueva (nov-2026): mínimo 350 tickets en el mes para cobrar cualquier bono.** B2C = WS, B2B = CS. Tickets = resueltos por el asignado, mes en hora Colombia, sin cerrados por merge (confirmar con Mike).

## K. Consolidar duplicados (SIN merge)
**Detección:** mismo **nombre completo** del worker en el asunto "Conversation with NOMBRE" (normalizar tildes/mayúsculas). El `requester_id` NO sirve: cada conversación crea un requester nuevo. Alta confianza = nombre de ≥2 palabras; nombres de una palabra ("Mar", "Javier") → verificar a mano. Mirar también la categoría: si el viejo tiene un caso concreto y el reciente es un handoff genérico, es el mismo caso (Mike lo confirmó).
**Regla de Mike (24-nov):** queda vivo el **más reciente**; los viejos se cierran. Nunca merge (genera conversaciones en blanco que se reabren).
**Por grupo** (`scripts/dedup_consolidate.py`, dry-run por defecto, `--apply` ejecuta):
1. Re-leer el estado en vivo: si el viejo ya no está new/open (alguien lo tomó) o el reciente no está abierto → saltar.
2. Si el viejo tuvo respuesta de un **agente humano** y el worker escribió después → la conversación sigue activa: no cerrar nada y avisar a Mike (alternativa: dejar el viejo y cerrar el nuevo). Ojo: Ada también aparece como autor `business`; no uses "mensaje del usuario tras el último business" como señal de actividad humana (da falsos positivos tras un handoff).
3. Nota interna en el **reciente** con el detalle de cada viejo (fecha, estado, categoría, asignado, nota de Nova, últimos mensajes). Si el viejo estaba con **otra área** (Camila, Luis, etc.), asignar el reciente a esa persona en WS, Open; si no, dejarlo como está.
4. Mensaje al worker **en el reciente** (Sunshine; template si WhatsApp >24 h, y entonces NO cerrar los viejos) con los IDs. Texto aprobado (sin proveedor/estados; el "en el transcurso del día" lo autorizó Mike, normalmente sería un ETA prohibido):
   - ES: "Hola, vemos que has abierto varias conversaciones por el mismo tema. Para atenderte mejor, vamos a seguir trabajando tu caso en esta conversación (ticket #NUEVO) y cerraremos la anterior (#VIEJO). En el transcurso del día te responderemos por aquí. Gracias por tu paciencia."
   - EN: "Hi, we noticed you have opened several conversations about the same topic. To help you better, we'll keep working on your case in this conversation (ticket #NEW) and we'll close the previous one (#OLD). We'll reply to you here during the day. Thanks for your patience."
   - PT: "Olá, vimos que você abriu várias conversas sobre o mesmo assunto. Para atendê-lo melhor, vamos continuar trabalhando no seu caso nesta conversa (ticket #NOVO) e vamos encerrar a anterior (#ANTIGO). Responderemos por aqui ao longo do dia. Obrigado pela sua paciência."
5. Cerrar el viejo según §L, con nota interna "🤖 Nova · Duplicado de #NUEVO … Cerrado sin merge (aprobado por Mike)".
Para grupos de 3+, un solo mensaje en el reciente listando todos los viejos.

## L. Cerrar (solve) un ticket sin disparar la encuesta CSAT
Orden obligatorio, ticket por ticket:
1. `zd.add_tags(id, ["dup_cerrado_nova","24_hours_tickets"])` → debe devolver True (usa `tags` con merge; `additional_tags` se ignora). Si es False, **no resolver**.
2. PUT con `custom_status_id` 22614180871444 + `custom_fields: [{"id":32273934250132,"value":"issue_request"}]` + nota interna. Si da 422, el error nombra el campo requerido (Category 22865771347348, Client ID 25216304678036…): completarlo solo si el dato es conocido; si no, dejar abierto y reportar.
3. Verificar ≥30 s después: `zd.csat_score(id) == "unoffered"`.
**Canario:** primero 1 ticket; si falla cualquier verificación (etiquetas, estado, score), parar y avisar. Nunca seguir "porque la señal principal salió bien".
Mensajería: el CSAT lo dispara el trigger `30949113742996` apenas pasa a solved; la exclusión es `tags no incluye dup_cerrado_nova` (ids.md §CSAT). Una encuesta ya ofrecida no se puede resetear por API.
