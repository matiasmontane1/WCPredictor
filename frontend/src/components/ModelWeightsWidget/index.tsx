import { useState } from 'react'
import { useModelWeights, useResetWeights } from '../../api/client'

const RESET_KEY = 'Matias2803'

export function ModelWeightsWidget() {
  const { data: weights, isLoading } = useModelWeights()
  const reset = useResetWeights()
  const [confirming, setConfirming] = useState(false)
  const [password, setPassword] = useState('')
  const [wrongKey, setWrongKey] = useState(false)

  if (isLoading) {
    return <div className="bg-slate-800 rounded-xl p-4 animate-pulse h-24" />
  }

  if (!weights) return null

  const xgPct = Math.round(weights.weight_xg * 100)
  const mktPct = 100 - xgPct

  function handleResetClick() {
    setConfirming(true)
    setPassword('')
    setWrongKey(false)
  }

  function handleCancel() {
    setConfirming(false)
    setPassword('')
    setWrongKey(false)
  }

  function handleConfirm() {
    if (password !== RESET_KEY) {
      setWrongKey(true)
      setPassword('')
      return
    }
    reset.mutate(undefined, {
      onSuccess: () => {
        setConfirming(false)
        setPassword('')
        setWrongKey(false)
      },
    })
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <div className="flex rounded-full overflow-hidden h-4 mb-2">
        <div className="bg-green-500 transition-all" style={{ width: `${xgPct}%` }} />
        <div className="bg-blue-500 transition-all" style={{ width: `${mktPct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-slate-400 mb-3">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500 inline-block" /> xG (Estadísticas) {xgPct}%
        </span>
        <span className="flex items-center gap-1">
          Cuotas Apuestas {mktPct}% <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-500">
          {weights.matches_evaluated} partido{weights.matches_evaluated !== 1 ? 's' : ''} evaluado{weights.matches_evaluated !== 1 ? 's' : ''}
          {weights.matches_evaluated < 5 && ' · Pesos se ajustan al llegar a 5'}
        </div>
        {!confirming && (
          <button
            onClick={handleResetClick}
            className="text-xs px-2 py-1 rounded-lg transition-colors bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-white"
          >
            Resetear
          </button>
        )}
      </div>

      {confirming && (
        <div className="mt-3 space-y-2">
          <p className="text-xs text-slate-400">Ingresá la clave para resetear los pesos:</p>
          <div className="flex gap-2">
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setWrongKey(false) }}
              onKeyDown={(e) => e.key === 'Enter' && handleConfirm()}
              placeholder="Clave"
              autoFocus
              className="flex-1 text-xs bg-slate-700 border border-slate-600 rounded-lg px-2 py-1.5 text-white placeholder-slate-500 focus:outline-none focus:border-slate-400"
            />
            <button
              onClick={handleConfirm}
              disabled={reset.isPending || !password}
              className="text-xs px-2 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white transition-colors"
            >
              {reset.isPending ? '...' : 'Confirmar'}
            </button>
            <button
              onClick={handleCancel}
              className="text-xs px-2 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-400 hover:text-white transition-colors"
            >
              Cancelar
            </button>
          </div>
          {wrongKey && (
            <p className="text-xs text-red-400">Clave incorrecta.</p>
          )}
        </div>
      )}
    </div>
  )
}
