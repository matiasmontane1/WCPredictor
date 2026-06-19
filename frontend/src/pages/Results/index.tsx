import { useState } from 'react'
import { useYesterdayMatches, useSubmitResult } from '../../api/client'
import type { MatchSummary } from '../../api/client'

export function Results() {
  const { data: matches, isLoading } = useYesterdayMatches()
  const submitResult = useSubmitResult()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [goals, setGoals] = useState<Record<number, { home: string; away: string }>>({})

  function handleSubmit(match: MatchSummary) {
    const g = goals[match.id] ?? { home: '', away: '' }
    const home = parseInt(g.home)
    const away = parseInt(g.away)
    if (isNaN(home) || isNaN(away) || home < 0 || away < 0) return

    submitResult.mutate(
      { matchId: match.id, goals_home: home, goals_away: away },
      {
        onSuccess: () => setEditingId(null),
      }
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
            const alreadyHasResult = hasResult(match)

            return (
              <div key={match.id} className="bg-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-white font-medium text-sm flex-1">{match.home_team}</span>
                  {alreadyHasResult && !isEditing ? (
                    <span className="text-green-400 font-bold text-lg mx-3">
                      {match.actual_home_goals} - {match.actual_away_goals}
                    </span>
                  ) : (
                    <span className="text-slate-400 text-xs mx-3">vs</span>
                  )}
                  <span className="text-white font-medium text-sm flex-1 text-right">{match.away_team}</span>
                  {alreadyHasResult && !isEditing && (
                    <button
                      onClick={() => startEdit(match)}
                      className="ml-3 text-slate-400 hover:text-white transition-colors"
                      title="Editar resultado"
                    >
                      ✏️
                    </button>
                  )}
                </div>

                {isEditing ? (
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
                      {submitResult.isPending ? '...' : 'Guardar'}
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="text-slate-400 hover:text-white px-2 py-2 text-sm"
                    >
                      ✕
                    </button>
                  </div>
                ) : !alreadyHasResult ? (
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
                      {submitResult.isPending ? '...' : 'Confirmar'}
                    </button>
                  </div>
                ) : (
                  <div className="text-center text-green-400 text-xs">
                    Feedback actualizado
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
