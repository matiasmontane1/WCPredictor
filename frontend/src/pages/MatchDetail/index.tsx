import { useParams, Link } from 'react-router-dom'
import { useMatchDetail } from '../../api/client'
import { SuggestionPanel } from '../../components/SuggestionPanel'
import { IntuitionValidator } from '../../components/IntuitionValidator'

export function MatchDetail() {
  const { id } = useParams<{ id: string }>()
  const matchId = Number(id)
  const { data: match, isLoading, error } = useMatchDetail(matchId)

  if (isLoading) {
    return (
      <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
        <div className="animate-pulse space-y-4">
          <div className="h-20 bg-slate-800 rounded-xl" />
          <div className="h-36 bg-slate-800 rounded-xl" />
          <div className="h-48 bg-slate-800 rounded-xl" />
        </div>
      </div>
    )
  }

  if (error || !match) {
    return (
      <div className="max-w-lg mx-auto px-4 pt-6 text-center text-slate-500">
        <p>Partido no encontrado.</p>
        <Link to="/" className="text-green-400 text-sm mt-2 block">← Volver</Link>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24 space-y-4">
      <Link to="/" className="text-slate-400 text-sm flex items-center gap-1 mb-2">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Volver
      </Link>

      <div className="bg-slate-800 rounded-xl p-4 text-center">
        <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">
          {match.phase?.replace(/_/g, ' ')}
        </div>
        <div className="flex items-center justify-center gap-4">
          <span className="text-white font-bold text-lg flex-1 text-right">{match.home_team}</span>
          <span className="text-slate-400 text-sm">vs</span>
          <span className="text-white font-bold text-lg flex-1">{match.away_team}</span>
        </div>
        {match.kickoff_time && (
          <div className="text-slate-400 text-xs mt-2">
            {new Date(match.kickoff_time).toLocaleString([], { hour: '2-digit', minute: '2-digit', weekday: 'short', day: 'numeric', month: 'short' })}
          </div>
        )}
        {match.metrics?.xg_home !== undefined && (
          <div className="flex justify-center gap-6 mt-3 text-xs text-slate-500">
            <span>xG local: <span className="text-slate-300">{match.metrics.xg_home?.toFixed(2)}</span></span>
            <span>xG visita: <span className="text-slate-300">{match.metrics.xg_away?.toFixed(2)}</span></span>
          </div>
        )}
      </div>

      {match.suggestions?.conservative || match.suggestions?.aggressive ? (
        <SuggestionPanel
          conservative={match.suggestions?.conservative}
          aggressive={match.suggestions?.aggressive}
        />
      ) : (
        <div className="bg-slate-800 rounded-xl p-4 text-center text-slate-500 text-sm">
          Sin sugerencias — sincronizá primero y configurá una fase activa
        </div>
      )}

      {match.score_distribution.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-4">
          <h3 className="text-slate-300 font-semibold mb-3">Distribución de Probabilidades</h3>
          <div className="space-y-1">
            {match.score_distribution.slice(0, 10).map((item) => (
              <div key={item.score} className="flex items-center gap-3">
                <span className="text-slate-400 text-xs w-4">#{item.rank}</span>
                <span className="text-white font-mono font-bold w-10">{item.score}</span>
                <div className="flex-1 bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${(item.probability / (match.score_distribution[0]?.probability || 1)) * 100}%` }}
                  />
                </div>
                <span className="text-slate-300 text-xs w-12 text-right">{(item.probability * 100).toFixed(1)}%</span>
                <span className="text-slate-500 text-xs w-14 text-right">{item.ev.toFixed(2)} EV</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <IntuitionValidator matchId={matchId} />
    </div>
  )
}
