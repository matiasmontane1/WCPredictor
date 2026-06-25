import { useState } from 'react'
import { usePastMatches, useSubmitResult, useActivePhase, FIXED_PHASES } from '../../api/client'
import type { MatchSummary, PhaseConfig } from '../../api/client'

function calcPoints(
  predicted: string,
  actualHome: number,
  actualAway: number,
  phase: PhaseConfig | null
): { pts: number; label: string } {
  if (!phase) return { pts: 0, label: '—' }
  const [ph, pa] = predicted.split('-').map(Number)
  if (isNaN(ph) || isNaN(pa)) return { pts: 0, label: '—' }

  const exactMatch = ph === actualHome && pa === actualAway
  const diffMatch = (ph - pa) === (actualHome - actualAway)
  const winnerMatch =
    (ph > pa && actualHome > actualAway) ||
    (ph === pa && actualHome === actualAway) ||
    (ph < pa && actualHome < actualAway)

  if (exactMatch) return { pts: phase.points_exact_score, label: 'Exacto' }
  if (diffMatch) return { pts: phase.points_goal_diff, label: 'Dif. goles' }
  if (winnerMatch) return { pts: phase.points_winner, label: 'Ganador' }
  return { pts: 0, label: 'Sin puntos' }
}

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const d = new Date(year, month - 1, day)
  return d.toLocaleDateString('es-CL', { weekday: 'long', day: 'numeric', month: 'long' })
}

export function Results() {
  const { data: matches, isLoading } = usePastMatches()
  const submitResult = useSubmitResult()
  const { data: activePhase } = useActivePhase()

  function phaseForId(phaseId?: number): PhaseConfig | null {
    if (!phaseId) return activePhase ?? null
    return FIXED_PHASES.find((p) => p.id === phaseId) ?? activePhase ?? null
  }
  const [editingId, setEditingId] = useState<number | null>(null)
  const [goals, setGoals] = useState<Record<number, { home: string; away: string }>>({})

  function handleSubmit(match: MatchSummary) {
    const g = goals[match.id] ?? { home: '', away: '' }
    const home = parseInt(g.home)
    const away = parseInt(g.away)
    if (isNaN(home) || isNaN(away) || home < 0 || away < 0) return
    submitResult.mutate(
      { matchId: match.id, goals_home: home, goals_away: away },
      { onSuccess: () => setEditingId(null) }
    )
  }

  function startEdit(match: MatchSummary) {
    setEditingId(match.id)
    setGoals((prev) => ({
      ...prev,
      [match.id]: {
        home: match.actual_home_goals?.toString() ?? '',
        away: match.actual_away_goals?.toString() ?? '',
      },
    }))
  }

  const [selectedType, setSelectedType] = useState<'conservative' | 'aggressive' | null>(null)

  const hasResult = (m: MatchSummary) =>
    m.actual_home_goals !== null && m.actual_home_goals !== undefined

  type SuggestionStats = { total: number; exact: number; diff: number; winner: number; none: number; points: number }
  const emptyStat = (): SuggestionStats => ({ total: 0, exact: 0, diff: 0, winner: 0, none: 0, points: 0 })

  const statsCons = emptyStat()
  const statsAgg = emptyStat()
  let countedMatches = 0

  for (const m of matches ?? []) {
    if (!hasResult(m)) continue
    const ah = m.actual_home_goals!
    const aa = m.actual_away_goals!

    if (m.suggestions?.conservative) {
      const r = calcPoints(m.suggestions.conservative.score, ah, aa, phaseForId(m.suggestions.conservative.phase_id))
      statsCons.total++
      statsCons.points += r.pts
      if (r.label === 'Exacto') statsCons.exact++
      else if (r.label === 'Dif. goles') statsCons.diff++
      else if (r.label === 'Ganador') statsCons.winner++
      else statsCons.none++
    }
    if (m.suggestions?.aggressive) {
      const r = calcPoints(m.suggestions.aggressive.score, ah, aa, phaseForId(m.suggestions.aggressive.phase_id))
      statsAgg.total++
      statsAgg.points += r.pts
      if (r.label === 'Exacto') statsAgg.exact++
      else if (r.label === 'Dif. goles') statsAgg.diff++
      else if (r.label === 'Ganador') statsAgg.winner++
      else statsAgg.none++
      countedMatches++
    }
  }

  // Group by date (already sorted desc from backend)
  const grouped: Record<string, MatchSummary[]> = {}
  for (const m of matches ?? []) {
    if (!grouped[m.match_date]) grouped[m.match_date] = []
    grouped[m.match_date].push(m)
  }
  const dates = Object.keys(grouped)

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
      <h1 className="text-white text-xl font-bold mb-4">Resultados</h1>

      {/* Accumulated points counter */}
      {countedMatches > 0 && (
        <div className="mb-3">
          <div className="grid grid-cols-2 gap-3">
            {(
              [
                { type: 'conservative', label: 'Conservadora', stats: statsCons, accent: 'green' },
                { type: 'aggressive',   label: 'Arriesgada',   stats: statsAgg,  accent: 'orange' },
              ] as const
            ).map(({ type, label, stats, accent }) => {
              const active = selectedType === type
              const borderCls = active
                ? accent === 'green' ? 'border-green-500' : 'border-orange-500'
                : accent === 'green' ? 'border-green-800' : 'border-orange-800'
              const bgCls = accent === 'green' ? 'bg-green-900/30' : 'bg-orange-900/30'
              const textCls = accent === 'green' ? 'text-green-400' : 'text-orange-400'
              const subCls  = accent === 'green' ? 'text-green-300' : 'text-orange-300'
              return (
                <button
                  key={type}
                  onClick={() => setSelectedType(active ? null : type)}
                  className={`${bgCls} border ${borderCls} rounded-xl p-3 text-center transition-all cursor-pointer`}
                >
                  <div className={`${textCls} text-xs font-medium mb-1`}>{label}</div>
                  <div className="text-white text-3xl font-bold">{stats.points}</div>
                  <div className={`${subCls} text-xs mt-1`}>pts acumulados</div>
                  <div className="text-slate-500 text-[10px] mt-1">{stats.total} partidos · toca para ver detalle</div>
                </button>
              )
            })}
          </div>

          {/* Detail panel */}
          {selectedType && (() => {
            const s = selectedType === 'conservative' ? statsCons : statsAgg
            const accent = selectedType === 'conservative' ? 'green' : 'orange'
            const label = selectedType === 'conservative' ? 'Conservadora' : 'Arriesgada'
            const headerCls = accent === 'green' ? 'text-green-400' : 'text-orange-400'
            return (
              <div className="mt-3 bg-slate-800 border border-slate-700 rounded-xl p-4">
                <div className={`text-xs font-semibold uppercase tracking-wider mb-3 ${headerCls}`}>
                  {label} — {s.total} partidos evaluados
                </div>
                <div className="grid grid-cols-4 gap-2 text-center mb-3">
                  {(
                    [
                      { key: 'exact',  label: 'Exacto',     value: s.exact,  color: 'text-green-400' },
                      { key: 'diff',   label: 'Dif. goles', value: s.diff,   color: 'text-yellow-400' },
                      { key: 'winner', label: 'Ganador',    value: s.winner, color: 'text-blue-400' },
                      { key: 'none',   label: 'Sin pts',    value: s.none,   color: 'text-slate-500' },
                    ] as const
                  ).map(({ key, label: l, value, color }) => (
                    <div key={key} className="bg-slate-700/60 rounded-lg py-2 px-1">
                      <div className={`text-2xl font-bold ${color}`}>{value}</div>
                      <div className="text-slate-400 text-[10px] mt-0.5">{l}</div>
                    </div>
                  ))}
                </div>
                {s.total > 0 && (
                  <div className="flex gap-1 rounded-lg overflow-hidden h-2">
                    {s.exact  > 0 && <div className="bg-green-500"  style={{ flex: s.exact }} />}
                    {s.diff   > 0 && <div className="bg-yellow-500" style={{ flex: s.diff }} />}
                    {s.winner > 0 && <div className="bg-blue-500"   style={{ flex: s.winner }} />}
                    {s.none   > 0 && <div className="bg-slate-600"  style={{ flex: s.none }} />}
                  </div>
                )}
                {s.total > 0 && (
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                    <span>0%</span>
                    <span>
                      {Math.round(((s.exact + s.diff + s.winner) / s.total) * 100)}% con puntos
                    </span>
                    <span>100%</span>
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-28 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && (!matches || matches.length === 0) && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">📅</div>
          <p className="font-medium">No hay partidos pasados aún</p>
          <p className="text-sm mt-1">Sincronizá para cargar el calendario</p>
        </div>
      )}

      {!isLoading && dates.length > 0 && (
        <div className="space-y-6">
          {dates.map((date) => (
            <div key={date}>
              <h2 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2 capitalize">
                {formatDate(date)}
              </h2>
              <div className="space-y-3">
                {grouped[date].map((match) => {
                  const g = goals[match.id] ?? { home: '', away: '' }
                  const isEditing = editingId === match.id
                  const saved = hasResult(match)
                  const ah = match.actual_home_goals!
                  const aa = match.actual_away_goals!
                  const cons = match.suggestions?.conservative
                  const agg = match.suggestions?.aggressive
                  const consPoints = saved && cons ? calcPoints(cons.score, ah, aa, phaseForId(cons.phase_id)) : null
                  const aggPoints = saved && agg ? calcPoints(agg.score, ah, aa, phaseForId(agg.phase_id)) : null

                  return (
                    <div key={match.id} className="bg-slate-800 rounded-xl p-4 space-y-3">
                      <div className="relative flex items-center min-h-[28px]">
                        <span className="flex-1 text-white font-medium text-sm pr-10">{match.home_team}</span>
                        <span className="flex-1 text-white font-medium text-sm text-right pl-10">{match.away_team}</span>
                        <div className="absolute left-1/2 -translate-x-1/2">
                          {saved && !isEditing ? (
                            <span className="text-green-400 font-bold text-lg whitespace-nowrap">{ah} - {aa}</span>
                          ) : (
                            <span className="text-slate-400 text-xs">vs</span>
                          )}
                        </div>
                      </div>

                      {saved && !isEditing && (consPoints || aggPoints) && activePhase && (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {cons && consPoints && (
                            <div className="bg-slate-700 rounded-lg p-2">
                              <div className="text-slate-400 mb-1">Conservador {cons.score}</div>
                              <div className={`font-bold ${consPoints.pts > 0 ? 'text-green-400' : 'text-slate-500'}`}>
                                {consPoints.pts} pts — {consPoints.label}
                              </div>
                            </div>
                          )}
                          {agg && aggPoints && (
                            <div className="bg-slate-700 rounded-lg p-2">
                              <div className="text-slate-400 mb-1">Arriesgado {agg.score}</div>
                              <div className={`font-bold ${aggPoints.pts > 0 ? 'text-green-400' : 'text-slate-500'}`}>
                                {aggPoints.pts} pts — {aggPoints.label}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {saved && !isEditing && (
                        <div className="flex justify-center">
                          <button
                            onClick={() => startEdit(match)}
                            className="text-slate-400 hover:text-slate-200 text-xs transition-colors"
                          >
                            Editar
                          </button>
                        </div>
                      )}

                      {(isEditing || !saved) && (
                        <div className="flex items-center gap-3">
                          <input
                            type="number" min={0} max={20} placeholder="0"
                            value={g.home}
                            onChange={(e) => setGoals((prev) => ({ ...prev, [match.id]: { ...g, home: e.target.value } }))}
                            className="w-16 bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-center focus:outline-none focus:border-green-500"
                          />
                          <span className="text-slate-400">-</span>
                          <input
                            type="number" min={0} max={20} placeholder="0"
                            value={g.away}
                            onChange={(e) => setGoals((prev) => ({ ...prev, [match.id]: { ...g, away: e.target.value } }))}
                            className="w-16 bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-center focus:outline-none focus:border-green-500"
                          />
                          <button
                            onClick={() => handleSubmit(match)}
                            disabled={submitResult.isPending}
                            className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-slate-600 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
                          >
                            {submitResult.isPending ? '...' : isEditing ? 'Actualizar' : 'Confirmar'}
                          </button>
                          {isEditing && (
                            <button onClick={() => setEditingId(null)} className="text-slate-400 hover:text-white px-2 py-2 text-sm">✕</button>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
