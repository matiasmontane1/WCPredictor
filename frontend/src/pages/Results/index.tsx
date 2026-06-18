import { useState } from 'react'
import { useAllMatches, useSubmitResult } from '../../api/client'

export function Results() {
  const { data: matches, isLoading } = useAllMatches()
  const submitResult = useSubmitResult()
  const [submitted, setSubmitted] = useState<Set<number>>(new Set())
  const [goals, setGoals] = useState<Record<number, { home: string; away: string }>>({})

  const pending = matches?.filter(
    (m) => m.actual_home_goals === null || m.actual_home_goals === undefined
  )

  function handleSubmit(matchId: number) {
    const g = goals[matchId]
    if (!g) return
    const home = parseInt(g.home)
    const away = parseInt(g.away)
    if (isNaN(home) || isNaN(away) || home < 0 || away < 0) return

    submitResult.mutate(
      { matchId, goals_home: home, goals_away: away },
      {
        onSuccess: () => {
          setSubmitted((prev) => new Set([...prev, matchId]))
        },
      }
    )
  }

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
      <h1 className="text-white text-xl font-bold mb-6">Cargar Resultados</h1>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2].map((i) => <div key={i} className="bg-slate-800 rounded-xl h-28 animate-pulse" />)}
        </div>
      )}

      {!isLoading && (!pending || pending.length === 0) && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">✅</div>
          <p className="font-medium">Sin resultados pendientes</p>
          <p className="text-sm mt-1">Sincronizá para cargar partidos del día</p>
        </div>
      )}

      {!isLoading && pending && pending.length > 0 && (
        <div className="space-y-3">
          {pending.map((match) => {
            const g = goals[match.id] ?? { home: '', away: '' }
            const isSubmitted = submitted.has(match.id)

            return (
              <div key={match.id} className="bg-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-white font-medium text-sm">{match.home_team}</span>
                  <span className="text-slate-400 text-xs">vs</span>
                  <span className="text-white font-medium text-sm">{match.away_team}</span>
                </div>

                {isSubmitted ? (
                  <div className="text-center text-green-400 text-sm font-medium py-2">
                    ✓ Resultado guardado — pesos actualizados
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <input
                      type="number"
                      min={0}
                      max={20}
                      placeholder="0"
                      value={g.home}
                      onChange={(e) => setGoals((prev) => ({ ...prev, [match.id]: { ...g, home: e.target.value } }))}
                      className="w-16 bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-center focus:outline-none focus:border-green-500"
                    />
                    <span className="text-slate-400">-</span>
                    <input
                      type="number"
                      min={0}
                      max={20}
                      placeholder="0"
                      value={g.away}
                      onChange={(e) => setGoals((prev) => ({ ...prev, [match.id]: { ...g, away: e.target.value } }))}
                      className="w-16 bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-center focus:outline-none focus:border-green-500"
                    />
                    <button
                      onClick={() => handleSubmit(match.id)}
                      disabled={submitResult.isPending}
                      className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-slate-600 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
                    >
                      Confirmar
                    </button>
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
