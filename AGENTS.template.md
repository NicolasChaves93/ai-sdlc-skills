# AGENTS.md — Orquestación SDLC y Estándares de Ingeniería

Este proyecto sigue una fábrica de software evolutiva en 7 fases con separación estricta entre **Negocio Puro**, **Arquitectura** e **Implementación por Niveles**.

## 1. Roles de Agentes y Repositorios
- **Gemini CLI (Orquestación, Negocio, Arquitectura y Notion):** Ejecuta Fases 0 a 3, modela procesos BPMN (`As-Is` → Simulación → `To-Be`), tablas DMN, diagramas C4/ERD/Secuencia, ADRs y sincroniza las 10 bases de datos de Notion (`NOTION_SCHEMA.md`).
- **Claude Code (Implementación, TDD y Refactor):** Ejecuta Fases 4 a 7 dentro de los repositorios (`api-<proyecto>`, `app-<proyecto>`, `infra-<proyecto>`) siguiendo TDD estricto y arquitectura hexagonal.

## 2. Compuertas Obligatorias (Zero-Skip Gates)
1. **Negocio Puro antes de Tecnología (Fases 1–2):** Prohibido mencionar frameworks, endpoints o tipos SQL en `RF`/`RNF`, reglas DMN (`BR-XX`), casos de uso, máquinas de estado o BPMN. Si cambia el flujo durante la construcción, actualizar primero el BPMN `To-Be` y las tablas DMN.
2. **ADR Aprobado antes de Código (Fase 3 Gate):** Prohibido crear carpetas de código o instalar dependencias sin un ADR de stack e infraestructura aprobado en Notion / `docs/adr/`.
3. **Construcción Evolutiva en 5 Niveles (Fase 4):**
   - **Nivel 1 (Núcleo Puro):** Entidades y reglas DMN (`BR-XX`) 100 % en memoria (`domain/`), sin imports de web ni BD. Tests unitarios primero (TDD).
   - **Nivel 2 (API en Memoria + Postman):** Repositorios en memoria + adaptadores HTTP (`FastAPI`/`Go`/etc.) + colección y entorno en `postman/` verificados con `postman collection run`.
   - **Nivel 3 (Persistencia Local SQLite):** Adaptadores SQLite + tests de integración.
   - **Nivel 4 (Producción & Carga):** Adaptadores PostgreSQL (pooler) + pruebas de concurrencia en `k6/` + despliegue.
   - **Nivel 5 (Interfaces):** Clientes frontend (`app-<proyecto>`) desacoplados sobre la API estabilizada.
4. **Sincronización de Corte y Freeze 24h:** Al cerrar cada nivel, actualizar la `Fase` del proyecto en Notion, aprobar diagramas Mermaid verificados y completar `Casos de prueba`. Respetar congelamiento de despliegues **24 horas antes** de eventos en vivo.

## 3. Frontera de Documentación (Repo vs. Notion)
- **Repositorio Git:** Código fuente hexagonal, tests (`unit/`, `integration/`), `docs/adr/`, `docs/simulador-bpmn.html`, `postman/`, `k6/`, `README.md` y `CHANGELOG.md`.
- **Notion (Hub Central):** `Proyectos activos`, `Documentos` (`PT-PP`, `PT-ERS`, `PT-ECU`, `PT-IGS`), `PoCs y decisiones`, `Requisitos`, `Reglas de negocio` (DMN), `Épicas`, `Historias y tareas`, `Iteraciones` y `Casos de prueba` (`RF -> HU -> BR -> Prueba`).

## 4. Convenciones
- Conversación y registros en Notion en **español**; identificadores de código, commits, ramas y rutas en **inglés**.
- Confirmar con el usuario antes de escribir en Notion o crear archivos de arquitectura.
