# Esquema Maestro Multi-Proyecto de Notion (ColombianCode)

> - Este archivo describe solo **datos**. Usa las herramientas de Notion que tenga disponibles tu cliente; sus nombres cambian entre clientes y versiones.
> - `data_source_id` sirve para consultar registros y leer el esquema; `database_id`, para crear filas.
> - Si una propiedad u opción no coincide con el esquema vivo, manda Notion: corrige este archivo.
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

## 3. Frontera de Documentación: Notion vs. Repositorio Git

- **Notion (Hub Central de Producto, Gestión y Trazabilidad):** `Proyectos activos`, `Documentos` (`PT-PP`, `PT-ERS`, `PT-ECU`, `PT-IGS`, Reviews/Retrospectivas), `PoCs y decisiones` (PoC y espejo de los ADR), `Requisitos`, `Reglas de negocio`, `Épicas`, `Historias y tareas`, `Iteraciones` y `Casos de prueba`.
- **Repositorio Git (Ingeniería Viva):** Código fuente hexagonal, tests automatizados de `BR-XX`, `README.md`, `CHANGELOG.md`, contratos OpenAPI/WebSocket, ADR (`docs/adr/`, fuente de verdad), migraciones SQL, archivos Docker y *runbooks* operativos (`docs/`).

## 4. Propiedades por base (leídas de Notion el 2026-11-25)

Formato: `Nombre` (tipo): valores permitidos. `título` es la propiedad principal de cada base. Las fórmulas, rollups e IDs automáticos son de solo lectura.

Opciones de `Módulo` (cambian por proyecto, verifica antes de usar): Sorteo · Mejores servidores · Trivia · Trivia interactiva · Administración · Portal participante · Infraestructura · General.
`Fase`: 1 Inicio · 2 Análisis · 3 Diseño · 4 Construcción · 5 Entrega · 6 Operación · 7 Cierre.
`Actores`: Participante · Presentador · Administrador · Operador.

### Clientes
- `Cliente` (título); `Estado` (select): Activo · Prospecto · En pausa · Cerrado
- `Tipo` (select): Canal / Aliado · Cliente directo
- `Sector` (select): Bienestar / Caja de compensación · Educación · Gobierno · Telecomunicaciones · Pyme · Otro
- `Servicios` (multi_select): Diagnóstico y consultoría · Software a la medida · Operación y soporte de eventos · TI como servicio
- Texto: `Contacto principal`, `Próxima acción`. Fecha: `Cliente desde`, `Fin de relación`, `Último contacto`, `Fecha próxima acción`
- Relación: `Proyectos`, `Eventos`, `Jornadas`

### Proyectos activos
- `Proyecto` (título); `Estado` (select): Ideación · En desarrollo · En operación · En pausa · Cerrado
- `Fase` (select); `Metodología` (select): Scrum · Kanban · Scrumban · Cascada
- `Tipo` (select): Producto propio · Software a la medida · Operación de eventos · TI como servicio · Consultoría
- `Repositorio` (url); `Inicio`, `Entrega` (fecha)
- Relación: `Cliente`, `Documentos`, `Requisitos`, `Reglas de negocio`, `Épicas`, `Historias y tareas`, `PoCs y decisiones`, `Iteraciones`, `Casos de prueba`

### Documentos
- `Documento` (título); `Estado` (select): Borrador · En revisión · Aprobado; `Fase` (select)
- `Tipo de documento` (select): Formal (PT) · Acta de constitución · Propuesta técnica · Levantamiento de requisitos · Diagrama ER · Arquitectura · Flujo / Secuencia · Prototipo / Mockups · Plan Scrum / Sprint · Presupuesto · Reunión con cliente · Acta de ajustes · Sprint Review / Retro · Otro
- `Plantilla` (select): PT-PP · Planteamiento del problema; PT-ERS · Especificación de requisitos; PT-ECU · Casos de uso; PT-IGS · Informe general del sistema; PT-PS · Prototipado; Propuesta técnica; Otro
- Texto: `Versión`, `Participantes`, `Responsable elaboración`, `Responsable aprobación`. Fecha: `Fecha`, `Fecha aprobación`
- Relación: `Proyecto`, `Historias relacionadas`, `Evento`

### PoCs y decisiones
- `Nombre` (título); `Código` (texto); `Tipo` (select): PoC · ADR
- `Estado` (select): En validación · Validada · Descartada · Aceptada
- Texto: `Hipótesis`, `Criterio de éxito`. Relación: `Proyecto`, `Historias`

### Requisitos
- `Requisito` (título); `Código` (texto); `Tipo` (select): Funcional (RF) · No funcional (RNF)
- `Estado` (select): Por validar · Aprobado · Implementado · Descartado
- `Prioridad` (select): Esencial · Ideal · Opcional; `Caso de uso` (select): Con CU especificado · Solo requisito
- `Categoría RNF` (select): Rendimiento · Seguridad · Disponibilidad · Usabilidad · Escalabilidad · Mantenibilidad · Legal
- `Módulo` (select); `Actores` (multi_select)
- Relación: `Proyecto`, `Historias`, `Reglas`. Solo lectura: `Cobertura`, `N.º historias`

### Reglas de negocio
- `Regla` (título); `Código`, `Descripción` (texto)
- `Estado` (select): Por validar · Validada · Descartada; `Categoría` (select): Trivias · Sorteos · General
- Relación: `Proyecto`, `Requisitos`, `Historias`, `Casos de prueba`. Solo lectura: `Cobertura`, `Pruebas`, `N.º historias`, `N.º pruebas`

### Épicas
- `Épica` (título); `Código` (ID automático); `Estado` (select): Por iniciar · En curso · Completa · Descartada
- `Prioridad` (select): Alta · Media · Baja; `Módulo` (select); `Objetivo`, `Valor para el negocio` (texto)
- Relación: `Proyecto`, `Historias`. Solo lectura: `Puntos totales`, `N.º historias`

### Historias y tareas
- `Historia / Tarea` (título); `ID` (automático); `Código` (fórmula)
- `Tipo` (select): Historia de Usuario · Regla de Negocio · Deuda Técnica / ADR · Soporte / Evento
- `Estado` (select): Backlog · Listo (DoR) · En Progreso (WIP Max 2) · En Pruebas · Terminado (DoD)
- `Prioridad (MoSCoW)` (select): Must · Should · Could · Won’t (por ahora) · Recurrente / Mantenimiento
- `Etapa` (select): Análisis · Diseño · Desarrollo · Ajustes · Pruebas; `Riesgo` (select): Bajo · Medio · Alto
- `Incremento` (select): Inc 1 · Inc 2 · Inc 3 · Inc 4 · Inc 5
- `Etiqueta de cobro` (select): SOP-N1 · SOP-N2 · SOP-N3 · DEV-N1 · DEV-N2 · DEV-N3 · DEV-N4 · INF-MEN · LOG-TRA · LOG-PAR · DES-JOR · No facturable
- `Módulo` (select); `Actores` (multi_select); `Facturado`, `Ruta crítica` (checkbox)
- Número: `Puntos (Fibonacci)`, `Valor de negocio`, `Horas reales`. Texto: `Para`, `Quiero`, `Responsable desarrollo`. Fecha: `Planificación`, `Fecha de asignación`
- Relación: `Proyecto`, `Épica`, `Iteración`, `Requisitos`, `Reglas`, `Casos de prueba`, `Documentos`, `PoCs / ADR`, `Depende de`, `Bloquea`
- Solo lectura: `Horas estimadas`, `Pruebas`, `N.º pruebas`

### Iteraciones
- `Iteración` (título); `Estado` (select): Planeada · En curso · Cerrada; `Objetivo` (texto); `Fecha` (fecha)
- Relación: `Proyecto`, `Historias`. Solo lectura: `N.º historias`, `Puntos planificados`

### Casos de prueba
- `Caso de prueba` (título); `Código` (ID automático); `Tipo` (select): Positivo · Negativo · Borde
- `Resultado` (select): Pendiente · Pasa · Falla; `Automatizada` (checkbox); `Escenario (Gherkin)` (texto)
- Relación: `Proyecto`, `Historia`, `Regla`
