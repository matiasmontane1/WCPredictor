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
