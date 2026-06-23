import { useActivePhase } from '../../api/client'
import { ModelWeightsWidget } from '../../components/ModelWeightsWidget'

export function Settings() {
  const { data: phase, isLoading } = useActivePhase()

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24 space-y-4">
      <h1 className="text-white text-xl font-bold mb-6">Ajustes</h1>

      <div>
        <h2 className="text-slate-300 font-semibold mb-3">Fase actual</h2>
        {isLoading && <div className="bg-slate-800 rounded-xl h-20 animate-pulse" />}
        {!isLoading && phase && (
          <div className="rounded-xl bg-green-900/30 border border-green-700 p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-white font-semibold">{phase.phase_name}</span>
            </div>
            <div className="text-slate-400 text-sm">
              Ganador: <span className="text-slate-200">{phase.points_winner} pts</span>
              {' · '}
              Dif. goles: <span className="text-slate-200">{phase.points_goal_diff} pts</span>
              {' · '}
              Exacto: <span className="text-slate-200">{phase.points_exact_score} pts</span>
            </div>
          </div>
        )}
        {!isLoading && !phase && (
          <p className="text-slate-500 text-sm text-center py-4">No hay fase activa</p>
        )}
      </div>

      <div>
        <h2 className="text-slate-300 font-semibold mb-3">Pesos del modelo</h2>
        <ModelWeightsWidget />
      </div>
      
    </div>
  )
}
