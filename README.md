# WCPredictor

Herramienta analítica personal para maximizar el rendimiento en una penca (quiniela) del Mundial de Fútbol. Combina un modelo de distribución de Poisson con probabilidades implícitas del mercado de apuestas para calcular el Valor Esperado (EV) de cada resultado posible y entregar sugerencias estratégicas diarias.

## Cómo funciona

El motor de predicción genera dos sugerencias por partido:

- **Conservadora**: el marcador con mayor EV ponderado — maximiza puntos esperados con menor riesgo.
- **Arriesgada**: marcador con alta probabilidad *y* buen EV, pensado para remontar posiciones en la penca.

Para cada partido, el sistema corre dos modelos en paralelo y los ensambla:

1. **Modelo A (xG / Elo)**: deriva tasas de gol esperadas a partir de ratings Elo scrapeados.
2. **Modelo B (Mercado)**: invierte las cuotas de las casas de apuestas para obtener lambdas implícitas de Poisson.
3. **Ensamble**: suma ponderada de las matrices de probabilidad de ambos modelos. Los resultados con más de 7 goles totales se penalizan ×0.1.
4. **Feedback loop**: tras cada partido, calcula el Brier Score de cada modelo y ajusta los pesos automáticamente (requiere ≥ 5 partidos evaluados).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy async |
| Base de datos (dev) | SQLite (`aiosqlite`) |
| Base de datos (prod) | PostgreSQL vía Supabase (`asyncpg`) |
| Scheduler | APScheduler — sincronización inteligente basada en los horarios de los partidos |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4 |
| Estado servidor | TanStack Query |
| Estado local | Zustand |
| Despliegue backend | Render (via `render.yaml`) |
| Despliegue frontend | Vercel |

## Estructura del proyecto

```
WCPredictor/
├── backend/
│   ├── main.py                     # Entry point FastAPI + scheduler
│   ├── requirements.txt
│   ├── render.yaml                 # Config de despliegue en Render
│   └── app/
│       ├── api/routes/             # Endpoints REST (/api/v1)
│       ├── core/                   # Config, base de datos
│       ├── models/                 # ORM (SQLAlchemy) y schemas (Pydantic)
│       ├── crud/                   # Operaciones de base de datos
│       └── services/
│           ├── engine/             # Motor de predicción
│           │   ├── calibrator.py   # Resuelve lambdas de mercado
│           │   ├── ensemble.py     # Combina matrices de probabilidad
│           │   ├── ev.py           # Cálculo de Valor Esperado
│           │   ├── feedback.py     # Actualización de pesos post-partido
│           │   └── suggester.py    # Selección conservadora/arriesgada
│           ├── scrapers/           # Odds API + Elo scraper
│           ├── sync_service.py     # Orquestador del ciclo de sync
│           └── smart_scheduler.py  # Programa syncs según horarios reales
├── frontend/
│   └── src/
│       ├── api/client.ts           # Todos los hooks de TanStack Query
│       ├── store/useAppStore.ts    # Zustand store
│       └── pages/                  # Dashboard, MatchDetail, Results, Stats, Settings
└── specs/                          # Documentación de diseño y modelo de datos
```

## Instalación local

### Requisitos previos

- Python 3.12+
- Node.js 20+
- Claves de API:
  - [football-data.org](https://www.football-data.org/client/register) — calendario y resultados
  - [the-odds-api.com](https://the-odds-api.com) — cuotas de apuestas (500 req/mes gratis)

### Backend

```bash
cd backend
cp .env.example .env
# Edita .env con tus API keys
pip install -r requirements.txt
uvicorn main:app --reload
```

El servidor queda disponible en `http://localhost:8000`. La primera vez crea `dev.db` (SQLite) e inserta la configuración inicial de fases.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La app queda disponible en `http://localhost:5173` y apunta al backend mediante el proxy de Vite.

## Variables de entorno

Crea `backend/.env` basándote en `.env.example`:

| Variable | Descripción |
|---|---|
| `ENV` | `development` (SQLite) o `production` (Postgres) |
| `FOOTBALL_DATA_API_KEY` | Clave de football-data.org |
| `ODDS_API_KEY` | Clave de the-odds-api.com |
| `DATABASE_URL` | URL de conexión (auto-configurada en dev) |
| `SUPABASE_URL` | Solo producción |
| `SUPABASE_KEY` | Solo producción |

## Modelo de datos principal

- `Match` — partidos del torneo (fuente: football-data.org)
- `ScrapedMetrics` — cuotas crudas y lambdas derivadas (1:1 con Match)
- `Suggestion` — sugerencias conservadora y arriesgada (1:N con Match, regeneradas en cada sync)
- `PredictionLog` — registro de feedback post-partido (si existe, el partido ya fue evaluado)
- `ModelWeights` — fila única con `weight_xg` + `weight_market` (suman 1)
- `PhaseConfig` — reglas de puntuación de la penca; solo una fila `is_active` a la vez

## Ciclo de sincronización

Al arrancar y cada día a las 00:05 CLT, el scheduler:

1. Importa el calendario completo del Mundial desde football-data.org
2. Evalúa partidos recién terminados y actualiza los pesos del modelo
3. Obtiene las cuotas del día desde the-odds-api
4. Calcula las lambdas Elo (con fallback a lambdas de mercado si falla el scraper)
5. Corre el motor para cada partido del día que no esté bloqueado (bloqueo = 10 min antes del pitido inicial)
6. Programa syncs adicionales optimizados según los horarios exactos de los partidos

## Páginas de la app

| Página | Descripción |
|---|---|
| Dashboard | Partidos del día con sugerencias conservadora/arriesgada |
| Match Detail | Distribución de probabilidades por marcador + validador de resultados manuales |
| Results | Historial de partidos pasados con rendimiento por tipo de sugerencia |
| Stats | Estadísticas históricas del Mundial |
| Settings | Configuración de fases (puntuación) y pesos del modelo |
