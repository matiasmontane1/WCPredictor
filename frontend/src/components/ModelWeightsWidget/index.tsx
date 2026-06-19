import { useState } from 'react'
import { useModelWeights, useResetWeights } from '../../api/client'

export function ModelWeightsWidget() {
  const { data: weights, isLoading } = useModelWeights()
  const reset = useResetWeights()
  const [confirming, setConfirming] = useState(false)

  if (isLoading) {
    return <div className="bg-slate-800 rounded-xl p-4 animate-pulse h-24" />
  }

  if (!weights) return null

  const xgPct = Math.round(weights.weight_xg * 100)
  const mktPct = 100 - xgPct

  function handleReset() {
    if (!confirming) { setConfirming(true); return }
    reset.mutate(undefined, { onSuccess: () => setConfirming(false) })
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h3 className="text-slate-300 font-semibold mb-3">Pesos del Modelo</h3>
      <div className="flex rounded-full overflow-hidden h-4 mb-2">
        <div className="bg-green-500 transition-all" style={{ width: `${xgPct}%` }} />
        <div className="bg-blue-500 transition-all" style={{ width: `${mktPct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mb-3">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> xG (FBref) {xgPct}%
        </span>
        <span className="flex items-center gap-1">
          Mercado {mktPct}% <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
        </span>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-500">
          {weights.matches_evaluated} partido{weights.matches_evaluated !== 1 ? 's' : ''} evaluado{weights.matches_evaluated !== 1 ? 's' : ''}
          {weights.matches_evaluated < 5 && ' · Pesos se ajustan al llegar a 5'}
        </div>
        <button
          onClick={handleReset}
          disabled={reset.isPending}
          className={`text-xs px-2 py-1 rounded-lg transition-colors ${
            confirming
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-white'
          }`}
        >
          {reset.isPending ? '...' : confirming ? 'Confirmar reset' : 'Resetear'}
        </button>
      </div>
      {confirming && !reset.isPending && (
        <p className="text-xs text-red-400 mt-2">
          Borra todos los logs de feedback y vuelve a 50/50. Tocá de nuevo para confirmar.
        </p>
      )}
    </div>
  )
}
