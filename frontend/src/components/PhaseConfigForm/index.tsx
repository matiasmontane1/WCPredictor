import { useState } from 'react'
import { useCreatePhase } from '../../api/client'

export function PhaseConfigForm() {
  const [phaseName, setPhaseName] = useState('')
  const [pointsWinner, setPointsWinner] = useState(1)
  const [pointsExact, setPointsExact] = useState(3)
  const [error, setError] = useState('')

  const create = useCreatePhase()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!phaseName.trim()) {
      setError('El nombre de la fase es requerido')
      return
    }
    create.mutate(
      { phase_name: phaseName, points_winner: pointsWinner, points_exact_score: pointsExact },
      {
        onSuccess: () => {
          setPhaseName('')
          setPointsWinner(1)
          setPointsExact(3)
        },
        onError: (err) => setError(err.message),
      }
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-slate-800 rounded-xl p-4 space-y-3">
      <h3 className="text-slate-300 font-semibold">Nueva Fase</h3>
      <input
        type="text"
        value={phaseName}
        onChange={(e) => setPhaseName(e.target.value)}
        placeholder="Ej: Grupos, Octavos, Final"
        className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-green-500 placeholder-slate-500"
      />
      <div className="flex gap-3">
        <div className="flex-1">
          <label className="text-slate-400 text-xs block mb-1">Pts por Ganador</label>
          <input
            type="number"
            min={0}
            value={pointsWinner}
            onChange={(e) => setPointsWinner(Number(e.target.value))}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-green-500"
          />
        </div>
        <div className="flex-1">
          <label className="text-slate-400 text-xs block mb-1">Pts por Exacto</label>
          <input
            type="number"
            min={0}
            value={pointsExact}
            onChange={(e) => setPointsExact(Number(e.target.value))}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:border-green-500"
          />
        </div>
      </div>
      {error && <p className="text-red-400 text-xs">{error}</p>}
      <button
        type="submit"
        disabled={create.isPending}
        className="w-full bg-green-500 hover:bg-green-600 disabled:bg-slate-600 text-white font-semibold py-2 rounded-lg transition-colors"
      >
        {create.isPending ? 'Guardando...' : 'Agregar Fase'}
      </button>
    </form>
  )
}
