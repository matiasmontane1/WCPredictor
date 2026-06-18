import type { SuggestionOut } from '../../api/client'

interface Props {
  conservative?: SuggestionOut
  aggressive?: SuggestionOut
}

function SuggestionCard({
  suggestion,
  type,
}: {
  suggestion?: SuggestionOut
  type: 'conservative' | 'aggressive'
}) {
  const isConservative = type === 'conservative'
  if (!suggestion) {
    return (
      <div className="flex-1 bg-slate-800 rounded-xl p-4 text-center text-slate-500 text-sm">
        Sin sugerencia
      </div>
    )
  }

  return (
    <div
      className={`flex-1 rounded-xl p-4 border ${
        isConservative
          ? 'bg-green-900/30 border-green-700'
          : 'bg-orange-900/30 border-orange-700'
      }`}
    >
      <div className={`text-xs font-semibold uppercase tracking-wide mb-2 ${isConservative ? 'text-green-400' : 'text-orange-400'}`}>
        {isConservative ? '🛡 Conservadora' : '⚡ Arriesgada'}
      </div>
      <div className="text-white font-bold text-4xl text-center mb-3">{suggestion.score}</div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Probabilidad</span>
          <span className={`font-semibold ${isConservative ? 'text-green-300' : 'text-orange-300'}`}>
            {(suggestion.probability * 100).toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">EV</span>
          <span className={`font-semibold ${isConservative ? 'text-green-300' : 'text-orange-300'}`}>
            {suggestion.ev.toFixed(2)} pts
          </span>
        </div>
      </div>
    </div>
  )
}

export function SuggestionPanel({ conservative, aggressive }: Props) {
  return (
    <div className="flex gap-3">
      <SuggestionCard suggestion={conservative} type="conservative" />
      <SuggestionCard suggestion={aggressive} type="aggressive" />
    </div>
  )
}
