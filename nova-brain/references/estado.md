# Estado vigente (actualizado 24-nov-2026) — revisar y actualizar al empezar

## Consolidación de duplicados del 24-nov (WS)
- Cola WS New+Open: 310 (185 new sin dueño, 287 de mensajería). 36 grupos de duplicados por nombre del worker.
- Ejecutado: 29 avisos enviados, 28 viejos cerrados (Type of Request = Issue), etiquetados `dup_cerrado_nova` + `24_hours_tickets` (verificado).
- **Incidente:** esos 28 recibieron la encuesta CSAT porque `additional_tags` se ignoró y las etiquetas no estaban al resolver. Etiquetados después para excluirlos de reportes. Pendiente: avisar al equipo de CSAT.
- **Pendientes de cierre (422):** #261106 (falta Category), #260746/#260747/#260753 (falta Client ID). Sus workers ya fueron avisados en el ticket reciente; alguien de CX debe completar el dato y cerrar.
- Saltados sin efectos: #259917, #260174 (ya no New/Open) y los grupos de #260929, #260414, #260312 (el reciente ya no estaba abierto).
- Trigger CSAT de mensajería modificado (ver ids.md §CSAT).

## Incidentes
- **Bre-B (Colombia) caído desde ~19-nov, sin ETA.** Producto integra otro proveedor. Mensaje aprobado: "Las transferencias por Bre-B a Colombia están temporalmente no disponibles y nuestro equipo ya está trabajando para restablecerlas. Tu dinero sigue seguro en tu cuenta y no se realizó ningún débito por los intentos fallidos. Mientras tanto, puedes enviar tu dinero a Colombia por transferencia bancaria tradicional. Te avisaremos por este medio apenas el servicio esté disponible de nuevo." ~40 tickets consolidados en Mike para cerrar cuando vuelva. Aura tiene una custom instruction temporal "Bre-B outage Nov 2026" → apagarla cuando vuelva.
- **Ecuador / token dinámico (20-nov desde ~18:15 UTC):** "Token validation failed", "hora del dispositivo incorrecta" o "no internet" al transferir a Ecuador. Causa: el servicio de transferencias a Ecuador falló; se fue restableciendo. Mensaje enviado: no es error del token, reintentar si la transferencia está Failed. El playbook de token en Aura tiene un aviso temporal ("Incidente token / Ecuador 20-nov") → quitarlo cuando esté estable. México con el mismo patrón (pendiente).

## Ausencias y reglas temporales
- **Sudu fuera:** sus tickets se reasignan a Justin (tarea horaria `trig_012YLSWgdiLrrYjignxEAbKT`). Apagarla cuando Mike diga que Sudu volvió. Ideal: reemplazar por trigger de Zendesk o el Router v11.6 en n8n.
- Fin de semana 21–22 nov: 56 tickets de otras áreas en IR (`scratchpad/wkend/moved_ir.json`); reapertura el lunes 23-nov 6:00 a. m. COL (`trig_01Hojtoz69pkqMg2DCsPzd6b`).

## Pendientes abiertos
- Hernán (258663/258668/258686/258707): facturas históricas desde 2023, pedidas a Manuel Castillo (BI).
- Claudia (259031): reenviar certificado con tarifa por hora cuando se arregle el generador.
- Producto (Boost): qué pasa con saldos bloqueados de Future Fund si el usuario no acepta los nuevos términos; 3% vs 5,25%.
- Payouts: tasa de cambio a COP antes de confirmar; cómo enviar a cuenta registrada con llave Bre-B; transferencias "completadas" que no llegan.
- Comisiones octubre: confirmar merges (Ezequiel), regla de productividad y Rockstar B2C (Pedro vs. Sudu).
