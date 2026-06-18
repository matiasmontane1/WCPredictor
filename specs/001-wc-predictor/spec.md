# Feature Specification: WCPredictor

**Feature Directory**: `specs/001-wc-predictor`
**Created**: 2026-06-17
**Status**: Ready for Planning

---

## Overview

WCPredictor es una herramienta analítica predictiva de uso personal y local diseñada para maximizar el rendimiento del usuario en una "penca" (polla/quiniela) del Mundial de Fútbol. En lugar de ser un simple registro manual, el sistema utiliza un modelo matemático ensamblado que cruza probabilidades del mercado de apuestas y estadísticas teóricas (Distribución de Poisson) para calcular el Valor Esperado (EV) de cada resultado posible, entregando sugerencias estratégicas diarias.

---

## Problem Statement

El usuario participa en una penca con un sistema de puntuación incremental por fases y necesita una ventaja matemática para tomar decisiones. Las predicciones basadas solo en la intuición o en el favoritismo popular no siempre son rentables. Se requiere un sistema automatizado que ingeste datos diarios, evalúe la probabilidad real de cada resultado y recomiende qué marcador predecir para maximizar los puntos acumulados, adaptándose dinámicamente a las reglas de cada fase del torneo.

---

## Target Users

- **Usuario único**: El propietario de la aplicación. Ejecuta la aplicación en un entorno local, configura las reglas de su penca y toma la decisión final sobre qué resultado ingresar en su torneo basándose en las recomendaciones del modelo.

---

## User Scenarios & Testing

### Escenario 1: Configurar los puntajes de la fase actual
- El usuario abre la app y accede al panel de configuración.
- Ingresa cuántos puntos otorga la fase actual por acertar al ganador y cuántos puntos extra otorga por acertar el resultado exacto.
- El sistema actualiza el motor de Valor Esperado (EV) con estos nuevos multiplicadores.

### Escenario 2: Sincronización diaria de datos (Scraping)
- Al comenzar el día, el usuario presiona "Sincronizar Hoy".
- El sistema ejecuta scrapers en segundo plano que extraen las cuotas de apuestas (1X2 y resultados exactos) y las métricas de Goles Esperados (xG) solo para los partidos de la jornada actual.
- Las probabilidades se normalizan y el modelo predictivo se actualiza al instante.

### Escenario 3: Evaluar sugerencias del motor predictivo
- El usuario selecciona un partido del día.
- El sistema presenta dos recomendaciones claras:
  - **Conservadora**: El resultado con mayor probabilidad estadística absoluta para asegurar puntos base.
  - **Arriesgada (Diferencial)**: Un resultado menos obvio pero con alto Valor Esperado (EV) para intentar remontar posiciones.

### Escenario 4: Validar la intuición del usuario
- En la vista del partido, el usuario tiene un "presentimiento" y escribe manualmente un resultado (ej. 3-1).
- Instantáneamente, el sistema procesa el input y devuelve la probabilidad real de que ocurra y el Valor Esperado estadístico de esa decisión.

### Escenario 5: Auto-aprendizaje y Feedback Loop
- Antes de iniciar la sincronización de una nueva jornada, el usuario ingresa manualmente los resultados reales de los partidos del día anterior en la interfaz.
- El algoritmo evalúa si el mercado de apuestas o el modelo de Poisson fue más preciso frente a la realidad y ajusta automáticamente los pesos de ponderación para las predicciones futuras.

---

## Functional Requirements

### Gestión de Ingesta y Scraping

- FR-01: El sistema debe contar con un disparador manual de "Sincronización Diaria".
- FR-02: El scraper debe extraer cuotas de Ganador/Empate/Visitante y de Resultados Exactos desde casas de apuestas, aplicables solo a los 90 minutos reglamentarios.
- FR-03: El scraper debe extraer métricas de Goles Esperados (xG) desde portales de estadísticas para usar como variable en el modelo de Poisson.
- FR-04: La ejecución de los scrapers debe ser asíncrona para no bloquear la interfaz y enfocarse solo en los equipos que juegan ese día.
- FR-05: El sistema debe normalizar las cuotas de apuestas eliminando el margen de ganancia (overround) para que la probabilidad implícita sume exactamente el 100%.

### Motor Predictivo y Lógica

- FR-06: El sistema debe calcular la probabilidad de cada marcador exacto utilizando un modelo ensamblado (Media Ponderada entre cuotas de mercado y distribución de Poisson).
- FR-07: El sistema debe permitir la configuración manual de los puntos otorgados por fase (Ganador y Marcador Exacto).
- FR-08: El motor debe calcular el Valor Esperado (EV) de cada posible marcador cruzando la probabilidad del resultado con los puntos configurados en la fase actual.
- FR-09: El sistema debe filtrar o penalizar matemáticamente los "outliers" (resultados atípicos con probabilidad marginal) para priorizar marcadores futbolísticamente realistas.

### Interfaz y Sugerencias

- FR-10: Para cada partido, la interfaz debe mostrar claramente una sugerencia Conservadora y una sugerencia Arriesgada basadas en el EV.
- FR-11: La interfaz debe incluir un campo reactivo (Validador de Intuición) que calcule en tiempo real la probabilidad y el EV de un marcador ingresado manualmente por el usuario.

### Feedback Loop y Ajuste de Pesos

- FR-12: El sistema debe proveer una interfaz rápida para que el usuario ingrese manualmente los marcadores finales de los partidos del día anterior.
- FR-13: El algoritmo debe evaluar retrospectivamente los resultados ingresados a mano y reajustar de forma automática los pesos de la media ponderada, otorgando mayor relevancia al modelo (Apuestas o Poisson) que haya demostrado mayor precisión empírica.

---

## Scoring Logic Detail

El núcleo de la aplicación no puntúa al usuario, sino que calcula la rentabilidad matemática de cada posible decisión. 

**1. Cálculo de Probabilidad Ensamblada:**
La probabilidad de un resultado exacto se calcula combinando ambas fuentes mediante una media ponderada con pesos dinámicos ($W$):
$P_{final}=(W_{poisson} \times P_{poisson})+(W_{apuestas} \times P_{apuestas})$
*Donde $P_{poisson}$ se obtiene mediante una distribución bivariada utilizando el xG scrapeado como tasa de ocurrencia $\lambda$, y $P_{apuestas}$ es la probabilidad implícita normalizada.*

**2. Optimización por Valor Esperado (EV):**
Una vez obtenida la $P_{final}$ de cada marcador, el sistema evalúa su rentabilidad según los puntos de la penca para la fase actual:
$EV=\sum(P(resultado) \times Puntos_{fase})$
El algoritmo utiliza este $EV$ para separar las sugerencias entre Conservadoras (priorizando la máxima $P_{final}$) y Arriesgadas (priorizando picos de rentabilidad en escenarios de menor consenso).

---

## Success Criteria

- SC-01: El proceso de "Sincronización Diaria" (scraping de cuotas y estadísticas) se completa correctamente sin bloquear la interfaz.
- SC-02: Las probabilidades de las casas de apuestas se normalizan correctamente, sumando siempre un 100% exacto tras eliminar el margen del casino.
- SC-03: El cálculo del EV y las sugerencias se actualizan en tiempo real al modificar la configuración de puntos de la fase.
- SC-04: El Validador de Intuición responde sin latencia al ingresar un marcador manual.
- SC-05: El sistema ignora automáticamente los tiempos extra y penales en fases eliminatorias, basando todo su cálculo en los 90 minutos regulares.

---

## Key Entities

| Entidad | Atributos principales |
|---|---|
| **ConfiguracionFase** | id, nombre_fase, puntos_ganador, puntos_resultado_exacto, multiplicador |
| **Partido** | id, fecha, equipo_local, equipo_visitante, estado, goles_local_real, goles_visitante_real |
| **MétricasScrapeadas** | partido_id, xg_local, xg_visitante, cuotas_1x2, cuotas_marcadores |
| **PesosModelo** | peso_apuestas, peso_poisson, factor_correccion_historico |
| **Sugerencia** | partido_id, marcador_recomendado, tipo (Conservador/Arriesgado), ev_calculado, probabilidad_porcentual |

---

## Scope Boundaries

**Incluye:**
- Algoritmo de media ponderada (Ensemble Model).
- Scraping diario de cuotas de apuestas y métricas xG.
- Cálculo de EV ajustado manualmente por fase del torneo.
- Ingreso manual de resultados reales para validación.
- Sistema de Auto-aprendizaje (Feedback loop de pesos basado en los resultados ingresados a mano).
- Validador manual de intuición en la interfaz.

**Excluye:**
- Simulador de llaves o cruces a futuro (bracket).
- Base de datos en la nube o sistema multi-usuario (es strictly local).
- Automatización directa de apuestas en sitios de terceros.
- Scraping automatizado de resultados pasados o históricos.
- Historial exhaustivo de todos los partidos del mundo (solo se procesa el Mundial día a día).

---

## Assumptions

- A-01: La aplicación correrá en un entorno local de un único usuario.
- A-02: Las estructuras HTML de los sitios de apuestas y estadísticas permiten el scraping, requiriendo un diseño modular por si el DOM cambia.
- A-03: La penca donde participa el usuario evalúa los resultados de las fases eliminatorias basándose únicamente en los 90 minutos reglamentarios.

---

## Dependencies & Risks

- D-01: El modelo de Poisson depende de la disponibilidad diaria de la métrica xG en portales deportivos.
- R-01: Los selectores CSS/XPath de los scrapers pueden romperse si los sitios web fuente se actualizan. Mitigación: Uso de interfaces modulares para los scrapers y pruebas unitarias rápidas.
- R-02: Falla total de extracción de datos. Mitigación: Implementar un fallback manual que permita ingresar cuotas o xG a mano en caso de caída del scraper.