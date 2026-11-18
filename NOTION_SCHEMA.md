# Esquema Maestro Multi-Proyecto de Notion (ColombianCode)

> **Uso para herramientas MCP de Notion:**
> - Para **consultar** registros (`API-query-data-source`): usa `data_source_id`.
> - Para **crear** filas nuevas (`API-post-page`): usa `parent: { "database_id": "<database_id>" }`.
> - **Regla Multi-Proyecto:** Estas bases son compartidas por todos los proyectos de ColombianCode. **Siempre filtra por la relación `Proyecto` activa** antes de calcular secuencias (`RF-01`, `HU-01`, etc.) o listar valores de `Módulo`.

## 1. Bases de Datos Maestras (Globales)

| # | Base de Datos | `database_id` (Crear) | `data_source_id` (Consultar) |
|---|---|---|---|
| 1 | Clientes | `41ae618d-5d53-8172-bcc6-d407e6e76d5c` | `41ae618d-5d53-81c8-89e4-000bfddd3d3e` |
| 2 | Proyectos activos | `41ae618d-5d53-8114-84ff-c6242f64b641` | `41ae618d-5d53-814a-8721-000b00330ce7` |
| 3 | Documentos | `41ae618d-5d53-8108-94d8-ccb73d7034f2` | `41ae618d-5d53-81d3-a930-000b170506e9` |
| 4 | PoCs y decisiones | `41ae618d-5d53-815d-9fb6-d48297f1dc72` | `41ae618d-5d53-81ea-bc3b-000b2e6c86e9` |
| 5 | Requisitos | `41ae618d-5d53-815d-a02e-fab86aa23944` | `41ae618d-5d53-810f-ad12-000b66155d6c` |
| 6 | Reglas de negocio | `41ae618d-5d53-8172-81e5-df5d18954a99` | `41ae618d-5d53-8156-a96a-000b8180cc4a` |
| 7 | Épicas | `41ae618d-5d53-819c-a5d5-e1edd5aaf08e` | `41ae618d-5d53-8152-a7f9-000b63a1bcab` |
| 8 | Historias y tareas | `41ae618d-5d53-8184-be52-f537089e5943` | `41ae618d-5d53-81bd-9697-000b39998e0b` |
| 9 | Iteraciones | `41ae618d-5d53-8147-a16b-fe3d424b9276` | `41ae618d-5d53-812e-ae57-000bf3a3593a` |
| 10 | Casos de prueba | `41ae618d-5d53-81c1-92e2-fd49db796abf` | `41ae618d-5d53-8171-b312-000b17fc8c7d` |

## 2. Reglas Universales del Embudo Relacional

- **Jerarquía:** `Cliente` (opcional en `Producto propio`) → `Proyecto` → Bases hijas.
- **Trazabilidad:** `Proyecto` → `Requisito (RF/RNF)` → `Épica` → `Historia (HU)` ↔ `Regla (BR)` → `Caso de prueba`.
- **Prefijos de Historias y tareas:** `HU-NN` (Historia funcional), `TEC-NN` (Tarea técnica / arquitectura / ADR), `SOP-NN` (Operación y soporte).
- **Numeración por proyecto:** Todo proyecto nuevo inicia en `RF-01`, `RNF-01`, `BR-01` y `01` (`HU-01` / `TEC-01`). En proyectos existentes, consulta primero los registros del proyecto para continuar desde el máximo vigente.
- **Módulos dinámicos:** Cada proyecto define sus propios módulos o dominios funcionales. Antes de etiquetar `Módulo`, inspecciona el esquema actual de la base o consulta al usuario qué módulos aplican al proyecto activo.
- **Plantillas de Documentos formales:** `PT-PP` (Planteamiento del problema), `PT-ERS` (Requisitos), `PT-ECU` (Casos de uso), `PT-IGS` (Informe general del sistema), `PT-PS` (Prototipado).
