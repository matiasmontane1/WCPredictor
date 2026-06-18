import { usePhaseConfigs, useActivatePhase, useDeletePhase } from '../../api/client'
import { PhaseConfigForm } from '../../components/PhaseConfigForm'
import { ModelWeightsWidget } from '../../components/ModelWeightsWidget'

export function Settings() {
  const { data: phases, isLoading } = usePhaseConfigs()
  const activate = useActivatePhase()
  const remove = useDeletePhase()

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24 space-y-4">
      <h1 className="text-white text-xl font-bold mb-6">Ajustes</h1>

      <div>
        <h2 className="text-slate-300 font-semibold mb-3">Fases de la Penca</h2>
        {isLoading && <div className="bg-slate-800 rounded-xl h-20 animate-pulse" />}
        {!isLoading && phases?.map((phase) => (
          <div
            key={phase.id}
            className={`flex items-center gap-3 p-3 rounded-xl mb-2 border ${
              phase.is_active
                ? 'bg-green-900/30 border-green-700'
                : 'bg-slate-800 border-slate-700'
            }`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-white font-medium">{phase.phase_name}</span>
                {phase.is_active && (
                  <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">Activa</span>
                )}
              </div>
              <div className="text-slate-400 text-xs mt-1">
                Ganador: {phase.points_winner} pt{phase.points_winner !== 1 ? 's' : ''} · Exacto: {phase.points_exact_score} pt{phase.points_exact_score !== 1 ? 's' : ''}
              </div>
            </div>
            <div className="flex gap-2">
              {!phase.is_active && (
                <button
                  onClick={() => activate.mutate(phase.id)}
                  className="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg transition-colors"
                >
                  Activar
                </button>
              )}
              {!phase.is_active && (
                <button
                  onClick={() => remove.mutate(phase.id)}
                  className="text-xs bg-slate-700 hover:bg-red-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-lg transition-colors"
                >
                  Eliminar
                </button>
              )}
            </div>
          </div>
        ))}
        {!isLoading && !phases?.length && (
          <p className="text-slate-500 text-sm text-center py-4">No hay fases configuradas aún</p>
        )}
      </div>

      <PhaseConfigForm />

      <ModelWeightsWidget />
    </div>
  )
}
