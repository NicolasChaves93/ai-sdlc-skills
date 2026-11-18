# Esquema y IDs Maestros de Notion (ColombianCode)

> **Uso para herramientas MCP de Notion:**
> - Para **consultar** registros (`API-query-data-source`): usa `data_source_id`.
> - Para **crear** filas nuevas (`API-post-page`): usa `parent: { "database_id": "<database_id>" }` (o `data_source_id` según la versión de API aceptada por el servidor).

## 1. Tabla Maestra de IDs

| # | Recurso / Base de Datos | `database_id` / `page_id` | `data_source_id` |
|---|---|---|---|
| 1 | 🚀 Plataforma de Juegos para Eventos v2 (Proyecto) | `41ae618d-5d53-813a-930c-c6b1aa70d536` (`page_id`) | Fila dentro de *Proyectos activos* |
| 2 | Clientes (Base maestra) | `41ae618d-5d53-8172-bcc6-d407e6e76d5c` | `41ae618d-5d53-81c8-89e4-000bfddd3d3e` |
| 3 | Proyectos activos | `41ae618d-5d53-8114-84ff-c6242f64b641` | `41ae618d-5d53-814a-8721-000b00330ce7` |
| 4 | Documentos | `41ae618d-5d53-8108-94d8-ccb73d7034f2` | `41ae618d-5d53-81d3-a930-000b170506e9` |
| 5 | PoCs y decisiones | `41ae618d-5d53-815d-9fb6-d48297f1dc72` | `41ae618d-5d53-81ea-bc3b-000b2e6c86e9` |
| 6 | Requisitos | `41ae618d-5d53-815d-a02e-fab86aa23944` | `41ae618d-5d53-810f-ad12-000b66155d6c` |
| 7 | Reglas de negocio | `41ae618d-5d53-8172-81e5-df5d18954a99` | `41ae618d-5d53-8156-a96a-000b8180cc4a` |
| 8 | Épicas | `41ae618d-5d53-819c-a5d5-e1edd5aaf08e` | `41ae618d-5d53-8152-a7f9-000b63a1bcab` |
| 9 | Historias y tareas | `41ae618d-5d53-8184-be52-f537089e5943` | `41ae618d-5d53-81bd-9697-000b39998e0b` |
| 10 | Iteraciones | `41ae618d-5d53-8147-a16b-fe3d424b9276` | `41ae618d-5d53-812e-ae57-000bf3a3593a` |
| 11 | Casos de prueba | `41ae618d-5d53-81c1-92e2-fd49db796abf` | `41ae618d-5d53-8171-b312-000b17fc8c7d` |

## 2. Valores Oficiales de `Módulo` (Requisitos e Historias)

1. `Sorteo`
2. `Mejores servidores`
3. `Trivia`
4. `Trivia interactiva`
5. `Administración`
6. `Portal participante`
7. `Infraestructura`
8. `General`

## 3. Reglas de Integridad Relacional

- **Embudo raíz:** `Cliente` (opcional en Producto propio) → `Proyecto` → Bases hijas.
- **Cadena de trazabilidad:** `Proyecto` → `Requisito (RF/RNF)` → `Épica` → `Historia (HU)` ↔ `Regla (BR)` → `Caso de prueba`.
- **Enlaces obligatorios al crear una Historia (`HU`):** `Proyecto`, `Épica`, `Requisitos`, `Módulo` (y `Reglas` / `Iteración` cuando aplique).
- **Enlaces obligatorios al crear un Caso de prueba:** `Proyecto`, `Historia`, `Regla` (nunca directo a `Requisito`).
- **Plantillas de Documentos formales:** `PT-PP` (Planteamiento del problema), `PT-ERS` (Requisitos), `PT-ECU` (Casos de uso), `PT-IGS` (Informe general del sistema), `PT-PS` (Prototipado).
