import { useModelWeights } from '../../api/client'

export function ModelWeightsWidget() {
  const { data: weights, isLoading } = useModelWeights()

  if (isLoading) {
    return <div className="bg-slate-800 rounded-xl p-4 animate-pulse h-24" />
  }

  if (!weights) return null

  const xgPct = Math.round(weights.weight_xg * 100)
  const mktPct = 100 - xgPct

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h3 className="text-slate-300 font-semibold mb-3">Pesos del Modelo</h3>
      <div className="flex rounded-full overflow-hidden h-4 mb-2">
        <div className="bg-green-500 transition-all" style={{ width: `${xgPct}%` }} />
        <div className="bg-blue-500 transition-all" style={{ width: `${mktPct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mb-3">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> xG (FBref) {xgPct}%</span>
        <span className="flex items-center gap-1">Mercado {mktPct}% <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /></span>
      </div>
      <div className="text-xs text-slate-500 text-center">
        {weights.matches_evaluated} partido{weights.matches_evaluated !== 1 ? 's' : ''} evaluado{weights.matches_evaluated !== 1 ? 's' : ''}
        {weights.matches_evaluated < 5 && ' · Los pesos se ajustan al llegar a 5'}
      </div>
    </div>
  )
}
