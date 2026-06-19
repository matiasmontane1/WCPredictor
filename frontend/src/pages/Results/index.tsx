import { useState } from 'react'
import { useYesterdayMatches, useSubmitResult, useActivePhase } from '../../api/client'
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

export function Results() {
  const { data: matches, isLoading } = useYesterdayMatches()
  const submitResult = useSubmitResult()
  const activePhase = useActivePhase()
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

  const hasResult = (m: MatchSummary) =>
    m.actual_home_goals !== null && m.actual_home_goals !== undefined

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
      <h1 className="text-white text-xl font-bold mb-6">Resultados de Ayer</h1>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-28 animate-pulse" />
          ))}
        </div>
      )}

      {!isLoading && (!matches || matches.length === 0) && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">📅</div>
          <p className="font-medium">No hubo partidos ayer</p>
        </div>
      )}

      {!isLoading && matches && matches.length > 0 && (
        <div className="space-y-3">
          {matches.map((match) => {
            const g = goals[match.id] ?? { home: '', away: '' }
            const isEditing = editingId === match.id
            const saved = hasResult(match)
            const ah = match.actual_home_goals!
            const aa = match.actual_away_goals!
            const cons = match.suggestions?.conservative
            const agg = match.suggestions?.aggressive
            const consPoints = saved && cons ? calcPoints(cons.score, ah, aa, activePhase) : null
            const aggPoints = saved && agg ? calcPoints(agg.score, ah, aa, activePhase) : null

            return (
              <div key={match.id} className="bg-slate-800 rounded-xl p-4 space-y-3">
                {/* Header partido */}
                <div className="flex items-center justify-between">
                  <span className="text-white font-medium text-sm flex-1">{match.home_team}</span>
                  {saved && !isEditing ? (
                    <span className="text-green-400 font-bold text-lg mx-3">{ah} - {aa}</span>
                  ) : (
                    <span className="text-slate-400 text-xs mx-3">vs</span>
                  )}
                  <span className="text-white font-medium text-sm flex-1 text-right">{match.away_team}</span>
                  {saved && !isEditing && (
                    <button
                      onClick={() => startEdit(match)}
                      className="ml-3 text-slate-400 hover:text-white transition-colors text-base"
                      title="Editar resultado"
                    >
                      ✏️
                    </button>
                  )}
                </div>

                {/* Puntos por sugerencia */}
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
                        <div className="text-slate-400 mb-1">Agresivo {agg.score}</div>
                        <div className={`font-bold ${aggPoints.pts > 0 ? 'text-green-400' : 'text-slate-500'}`}>
                          {aggPoints.pts} pts — {aggPoints.label}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Formulario */}
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
      )}
    </div>
  )
}
