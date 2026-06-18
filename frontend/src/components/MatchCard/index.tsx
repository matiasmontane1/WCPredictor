import { Link } from 'react-router-dom'
import type { MatchSummary } from '../../api/client'

interface Props {
  match: MatchSummary
}

function formatKickoff(iso?: string): string {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function MatchCard({ match }: Props) {
  return (
    <Link to={`/match/${match.id}`} className="block bg-slate-800 rounded-xl p-4 hover:bg-slate-700 transition-colors">
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs text-slate-400 uppercase tracking-wide">{match.phase?.replace(/_/g, ' ')}</span>
        {match.kickoff_time && (
          <span className="text-xs text-slate-400">{formatKickoff(match.kickoff_time)}</span>
        )}
      </div>

      <div className="flex items-center justify-between mb-4">
        <span className="text-white font-semibold text-sm flex-1">{match.home_team}</span>
        <span className="text-slate-400 text-xs mx-3">vs</span>
        <span className="text-white font-semibold text-sm flex-1 text-right">{match.away_team}</span>
      </div>

      {match.suggestions ? (
        <div className="flex gap-2">
          {match.suggestions.conservative && (
            <div className="flex-1 bg-green-900/40 border border-green-700 rounded-lg px-3 py-2">
              <div className="text-xs text-green-400 font-medium mb-1">Conservadora</div>
              <div className="text-white font-bold text-lg">{match.suggestions.conservative.score}</div>
              <div className="text-green-300 text-xs">{(match.suggestions.conservative.probability * 100).toFixed(1)}%</div>
            </div>
          )}
          {match.suggestions.aggressive && (
            <div className="flex-1 bg-orange-900/40 border border-orange-700 rounded-lg px-3 py-2">
              <div className="text-xs text-orange-400 font-medium mb-1">Arriesgada</div>
              <div className="text-white font-bold text-lg">{match.suggestions.aggressive.score}</div>
              <div className="text-orange-300 text-xs">EV: {match.suggestions.aggressive.ev.toFixed(2)}</div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-slate-500 text-sm py-2">
          {match.has_metrics ? 'Configurá una fase para ver sugerencias' : 'Sin datos — sincronizá primero'}
        </div>
      )}
    </Link>
  )
}
