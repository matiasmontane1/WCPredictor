import { useWCStats } from '../../api/client'

const MARGIN_LABELS: Record<string, string> = {
  draw: 'Empate',
  one_goal: 'Diferencia 1',
  two_goals: 'Diferencia 2',
  three_plus: 'Diferencia 3+',
}

const MARGIN_COLORS: Record<string, string> = {
  draw: 'bg-slate-500',
  one_goal: 'bg-blue-500',
  two_goals: 'bg-yellow-500',
  three_plus: 'bg-red-500',
}

export function Stats() {
  const { data, isLoading } = useWCStats()

  if (isLoading) {
    return (
      <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-800 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (!data || data.total_matches === 0) {
    return (
      <div className="max-w-lg mx-auto px-4 pt-6 pb-24 text-center text-slate-500 text-sm">
        <p className="mt-8">Aún no hay partidos finalizados en el Mundial.</p>
      </div>
    )
  }

  const maxScorelineCount = data.top_scorelines[0]?.count ?? 1
  const maxGoalsCount = Math.max(...data.total_goals_distribution.map((g) => g.count), 1)

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24 space-y-4">
      {/* Header */}
      <div className="bg-slate-800 rounded-xl p-4 text-center">
        <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Mundial 2026</div>
        <div className="text-3xl font-bold text-white">{data.total_matches}</div>
        <div className="text-slate-400 text-sm">partidos jugados</div>
      </div>

      {/* Último partido integrado */}
      {data.last_match && (
        <div className="bg-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">Último partido integrado</div>
          <div className="flex items-center justify-between">
            <div className="text-white font-semibold text-sm">{data.last_match.home_team}</div>
            <div className="text-green-400 font-bold text-lg font-mono px-3">{data.last_match.score}</div>
            <div className="text-white font-semibold text-sm text-right">{data.last_match.away_team}</div>
          </div>
          {data.last_match.kickoff_time && (
            <div className="text-slate-500 text-xs text-center mt-1">
              {new Date(data.last_match.kickoff_time).toLocaleString([], {
                weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
              })}
            </div>
          )}
        </div>
      )}

      {/* Top 5 marcadores */}
      <div className="bg-slate-800 rounded-xl p-4">
        <h3 className="text-slate-300 font-semibold mb-3">Top 5 Marcadores más Frecuentes</h3>
        <div className="space-y-2">
          {data.top_scorelines.map((item, idx) => (
            <div key={item.score} className="flex items-center gap-3">
              <span className="text-slate-500 text-xs w-4">#{idx + 1}</span>
              <span className="text-white font-mono font-bold w-10">{item.score}</span>
              <div className="flex-1 bg-slate-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${(item.count / maxScorelineCount) * 100}%` }}
                />
              </div>
              <span className="text-slate-300 text-xs w-8 text-right">{item.count}x</span>
              <span className="text-slate-500 text-xs w-12 text-right">{item.pct}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Diferencia de goles */}
      <div className="bg-slate-800 rounded-xl p-4">
        <h3 className="text-slate-300 font-semibold mb-3">Diferencia de Goles</h3>
        <div className="space-y-2">
          {(['draw', 'one_goal', 'two_goals', 'three_plus'] as const).map((key) => {
            const pct = data.margin_distribution[key] ?? 0
            return (
              <div key={key} className="flex items-center gap-3">
                <span className="text-slate-400 text-xs w-24 shrink-0">{MARGIN_LABELS[key]}</span>
                <div className="flex-1 bg-slate-700 rounded-full h-2">
                  <div
                    className={`${MARGIN_COLORS[key]} h-2 rounded-full`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-slate-300 text-xs w-12 text-right">{pct}%</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Goles totales por partido */}
      <div className="bg-slate-800 rounded-xl p-4">
        <h3 className="text-slate-300 font-semibold mb-3">Goles Totales por Partido</h3>
        <div className="flex items-end gap-2 h-28 mt-2">
          {data.total_goals_distribution.map((item) => (
            <div key={item.goals} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-slate-400 text-xs">{item.pct > 0 ? `${item.pct}%` : ''}</span>
              <div className="w-full flex items-end" style={{ height: '64px' }}>
                <div
                  className="w-full bg-green-500 rounded-t"
                  style={{ height: `${(item.count / maxGoalsCount) * 64}px`, minHeight: item.count > 0 ? 4 : 0 }}
                />
              </div>
              <span className="text-slate-400 text-xs">{item.goals}</span>
            </div>
          ))}
        </div>
        <div className="text-center text-xs text-slate-500 mt-1">goles en el partido</div>
      </div>

      {/* Ambos anotan */}
      <div className="bg-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div>
          <div className="text-slate-300 font-semibold">Ambos Anotan (BTTS)</div>
          <div className="text-slate-500 text-xs mt-0.5">Partidos donde ambos equipos marcaron</div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-green-400">{data.btts_percentage}%</div>
          <div className="text-slate-500 text-xs">de los partidos</div>
        </div>
      </div>
    </div>
  )
}
