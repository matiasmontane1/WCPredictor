import { useParams, Link } from 'react-router-dom'
import { useMatchDetail } from '../../api/client'
import type { TeamStats } from '../../api/client'
import { SuggestionPanel } from '../../components/SuggestionPanel'
import { IntuitionValidator } from '../../components/IntuitionValidator'
import { getFlag } from '../../utils/flags'

function FormBadge({ result }: { result: string }) {
  const color = result === 'W' ? 'bg-green-500' : result === 'D' ? 'bg-yellow-500' : 'bg-red-500'
  return <span className={`${color} text-white text-xs font-bold w-5 h-5 flex items-center justify-center rounded-full`}>{result}</span>
}

function TeamStatsCard({ name, stats }: { name: string; stats: TeamStats }) {
  const form = stats.form.split(',').filter(Boolean)
  return (
    <div className="flex-1 space-y-2">
      <div className="text-center">
        <div className="text-2xl mb-1">{getFlag(name)}</div>
        <div className="text-white font-semibold text-sm">{name}</div>
        <div className="text-slate-500 text-xs">últimos {stats.sample_size} partidos</div>
      </div>
      <div className="grid grid-cols-2 gap-1 text-xs">
        <div className="bg-slate-700 rounded-lg p-2 text-center">
          <div className="text-slate-400">Goles/partido</div>
          <div className="text-green-400 font-bold">{stats.avg_goals_scored.toFixed(1)}</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-2 text-center">
          <div className="text-slate-400">Recibe/partido</div>
          <div className="text-red-400 font-bold">{stats.avg_goals_conceded.toFixed(1)}</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-2 text-center">
          <div className="text-slate-400">Clean sheets</div>
          <div className="text-blue-400 font-bold">{(stats.clean_sheet_pct * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-2 text-center">
          <div className="text-slate-400">Resultado más común</div>
          <div className="text-white font-bold">{stats.most_common_result}</div>
        </div>
      </div>
      <div className="flex gap-1 justify-center">
        {form.map((r, i) => <FormBadge key={i} result={r} />)}
      </div>
    </div>
  )
}

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

      {(match.home_stats || match.away_stats) && (
        <div className="bg-slate-800 rounded-xl p-4">
          <h3 className="text-slate-300 font-semibold text-sm mb-3 text-center">Estadísticas recientes</h3>
          <div className="flex gap-4">
            {match.home_stats && <TeamStatsCard name={match.home_team} stats={match.home_stats} />}
            {match.home_stats && match.away_stats && <div className="w-px bg-slate-700" />}
            {match.away_stats && <TeamStatsCard name={match.away_team} stats={match.away_stats} />}
          </div>
        </div>
      )}

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
