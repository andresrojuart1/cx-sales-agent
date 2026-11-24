# IDs y constantes (Ontop · getontop.zendesk.com)

## Grupos Zendesk
| Grupo | ID |
|---|---|
| Worker Support (WS, B2C) | 22616861202452 |
| Company Support (CS, B2B) | 23897889259668 |
| Payouts (side conversations) | 27679198971284 |
| Tech | 28142490569620 |
| Product Operations | 40661799249812 |
| Account Management | 26268947372308 |
| Risk & Compliance | 29797988546836 |
| Card Ops | 30916073349396 |
| FinOps | 32168271619348 |
| Finance | 30915833430548 |
| Legal | 31724066883092 |
| Worker Journey | 49225756075028 |

Al reasignar, verificar que el grupo no cambie (Zendesk a veces lo mueve); si cambia, volver a poner el grupo correcto.

## Estados personalizados (custom_status_id)
| Estado | ID |
|---|---|
| 1. New | 22614180829972 |
| 2. Open | 22614166894100 |
| 3. Waiting for requester response (pending) | 25685916283028 |
| 4. Externally raised (hold) | 26417816117780 |
| 5. Internally raised (hold) | 31769974642836 |
| 6. Solved | 22614180871444 |

Para resolver, Zendesk puede exigir campos según el ticket (ver "Requeridos para resolver" abajo); si faltan y no se pueden completar, dejar en Waiting (se cierra solo).

## Campos
- Category (REQUIRED): `22865771347348`
- **Misclassified Ticket: `35555524967060` — NUNCA tocar.**
- **Requeridos para resolver (si faltan → 422 con el campo en el error):** Type of Request `32273934250132` (valores: `issue_request`, `question_request`, `product_feedback_request`, `internal_process_request`; no existe "duplicado", Mike eligió `issue_request` para duplicados), Category `22865771347348`, Client ID `25216304678036` (algunos tickets lo exigen). Worker ID `25216293967380` y Worker Email `26816172973460` no son obligatorios a nivel de campo, pero pueden serlo por formulario.
- Estado Solved: `custom_status_id` 22614180871444.

## CSAT (encuesta de satisfacción)
- Trigger mensajería **"Request customer satisfaction rating (Messaging)" `30949113742996`**: se dispara al pasar a solved. El 24-nov-2026 Nova le agregó (con OK de Mike) la condición `tags no incluye dup_cerrado_nova`. El original solo tenía `via_id` y `status = solved`; su acción es `notification_default_messaging_customer_satisfaction_survey` → `requester_id`.
- Automatizaciones CSAT (`25002517839508`, `24524636961940`): excluyen la etiqueta `24_hours_tickets` (usada en ~25.000 tickets; no la quites ni la reutilices para otra lógica).
- Para cerrar sin encuesta: ambas etiquetas, `dup_cerrado_nova` y `24_hours_tickets`.
- PUT a triggers: hay que reenviar `actions` junto con `conditions` o da 422 ("must contain at least one action").

## Equipo CX (Zendesk user id · Slack)
| Persona | Zendesk | Dominio |
|---|---|---|
| Mike / Maicol Rojas (Head of CX) | 42677627758740 · Slack U09NCCJJ2UT | — |
| Justin Mejia | 54788295418644 | Payouts & pay-ins |
| Sudu (Sudarshan Krishnamurthy) | 24567978777492 | Payouts & pay-ins |
| Brisa Calero | 47071350698516 | Onboarding & access |
| Cristian Echeverria | 48493524357268 | Onboarding & access |
| Jaime Tellez | 55350915332244 | Financial Services (PA, Boost, Reserve, card) |
| Carolina Gutiérrez | 32288140085012 | Financial Services |
| Samuel Jimenez | 40230868739348 | B2B · cuentas top |
| Miguel Cotes | 28269839522452 · Slack U06LW3ASH7D | B2B · cuentas top |
| Ontop Support (tm-support3@getontop.com) | 26024622590356 | autor para respuestas públicas por correo en nombre del equipo |

Ex-equipo (suspendidos, solo para comisiones): Pedro Vega 32530906468244, Ruben Monterrosa 27264131564820, Ezequiel Coiradas 26228468813204, Yaritza Vanegas 32240251894164.

## Personas de otras áreas para escalar (dentro del grupo WS)
| Área | Persona | Zendesk |
|---|---|---|
| Tech (face match, Tax ID, cambio de documento, bugs) | Luis Caicedo "Lucho" | 26261757377556 |
| Compliance (KYC) | Jorge Querales | 28706962534164 |
| Payouts | Camila Garcia | 30873580217236 |
| Paycheck Advance | Slenny Velásquez | 38334829140372 |
| BI / Data | Manuel Castillo (Data Lead) | Slack U044TREBBA8 |

Otras personas Slack: Daniela Linero (CCO) U02DM7JED4N, DM Mike–Daniela D0APT39QGLS.

## Sunshine (mensajería)
- Endpoint: `https://{subdomain}.zendesk.com/sc/v2/apps/{SUNCO_APP_ID}/conversations/{conv}/messages` (auth básica SUNCO_KEY_ID:SUNCO_KEY_SECRET).
- El `conversation_id` sale de los audits del ticket: evento `ChatStartedEvent` → `value.conversation_id`.
- Autor: `{"type":"business","displayName":"Ontop Support"}`.
- Integración WhatsApp real: `65d7c6897da3f1e6aaa17aa0`. **Nunca** `663b9636d2bd090b34b10e2b` (Prueba CS).
- Template de reactivación: `reactivar_conversacion`, idioma `es` o `en` (body en `scripts/sunco.py`).
- Adjuntar archivo: POST `/attachments?access=public&for=message&conversationId=…` y luego mensaje `{"type":"file","mediaUrl":…}`.

## Ada (Aura)
- Canal web chat para test cases: `bmF0aXZlLWNoYXQtNjg2NzNmN2JjZDA3ODA1YjI0NjRlYzJh`
- Variables: user_type `68814c17e810119b0b0542e0` = worker · b2b_or_b2c `686ffa068683ea94a377d536` = B2C · user_email `68a3989d9bee25e3ce725959` · contrato `69055c68309cd330d5c03334` (CA…) · canal `6870438f82b7bb083acbc81a` (whatsapp).
- Code tool con ONSIGHT_TOKEN (sandbox Onsight): `6ab853b4edbc966686882620` (inputs `{"email":"","question":""}`, máx. 10 requests por corrida).
- Conector Onsight: `0ef9e62e-cb8e-4f3f-a3fc-1ba33f25d301` · MCP `https://mcp.onsight.getontop.com/mcp` · tool `onsight_execute_sql`.
- Playbooks clave: Worker Wallet Transfer Status v2 `6aa7f896d4af59a7d0ebccb4` · Acceso, bloqueos y token dinámico `6ad3d51771609441cea56628`.
- Fuente de chunks del Help Center: knowledge_source `aura-kb-zendesk-chunks`.

## Onsight (tablas útiles, solo SELECT)
`process_data.contractor` (cod_contractor, des_email, KYC, wallet), `process_data.contract` (cod_contract, id_client, des_contract_type, pay_per_thing, amt_compensation_usd, amt_monthly_compensation, is_active_contract), `process_data.wallet_transaction`, `process_data.invoice`, `process_data.client` (id_client, cod_client, des_trade_name), `process_data.vw_team_users` (admins de clientes).

## Slack
- DM a Mike: `U09NCCJJ2UT` · canal piloto con áreas: `#temp-zendesk-tickets` C0CHSEB9PD5 · reportes técnicos: `#ops-run-process`.
