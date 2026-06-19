import { useState } from 'react'
import { usePhaseConfigs, useActivatePhase, useDeactivatePhase, useUpdatePhase, useDeletePhase } from '../../api/client'
import type { PhaseConfig } from '../../api/client'
import { PhaseConfigForm } from '../../components/PhaseConfigForm'
import { ModelWeightsWidget } from '../../components/ModelWeightsWidget'

interface EditState {
  phase_name: string
  points_winner: number
  points_goal_diff: number
  points_exact_score: number
}

function PhaseCard({ phase }: { phase: PhaseConfig }) {
  const activate = useActivatePhase()
  const deactivate = useDeactivatePhase()
  const update = useUpdatePhase()
  const remove = useDeletePhase()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState<EditState>({
    phase_name: phase.phase_name,
    points_winner: phase.points_winner,
    points_goal_diff: phase.points_goal_diff,
    points_exact_score: phase.points_exact_score,
  })

  function startEdit() {
    setForm({
      phase_name: phase.phase_name,
      points_winner: phase.points_winner,
      points_goal_diff: phase.points_goal_diff,
      points_exact_score: phase.points_exact_score,
    })
    setEditing(true)
  }

  function saveEdit() {
    update.mutate({ id: phase.id, data: form }, { onSuccess: () => setEditing(false) })
  }

  return (
    <div className={`rounded-xl mb-2 border ${phase.is_active ? 'bg-green-900/30 border-green-700' : 'bg-slate-800 border-slate-700'}`}>
      {/* View mode */}
      {!editing && (
        <div className="flex items-center gap-3 p-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-white font-medium">{phase.phase_name}</span>
              {phase.is_active && (
                <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">Activa</span>
              )}
            </div>
            <div className="text-slate-400 text-xs mt-1">
              Ganador: {phase.points_winner} · Dif: {phase.points_goal_diff} · Exacto: {phase.points_exact_score} pts
            </div>
          </div>
          <div className="flex gap-1.5">
            {!phase.is_active && (
              <button
                onClick={() => activate.mutate(phase.id)}
                disabled={activate.isPending}
                className="text-xs bg-green-600 hover:bg-green-700 text-white px-2.5 py-1.5 rounded-lg transition-colors"
              >
                Activar
              </button>
            )}
            {phase.is_active && (
              <button
                onClick={() => deactivate.mutate(phase.id)}
                disabled={deactivate.isPending}
                className="text-xs bg-slate-600 hover:bg-slate-500 text-white px-2.5 py-1.5 rounded-lg transition-colors"
              >
                Desactivar
              </button>
            )}
            <button
              onClick={startEdit}
              className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg transition-colors"
            >
              Editar
            </button>
            <button
              onClick={() => remove.mutate(phase.id)}
              disabled={remove.isPending || phase.is_active}
              title={phase.is_active ? 'Desactivá la fase antes de eliminarla' : ''}
              className="text-xs bg-slate-700 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg transition-colors"
            >
              Borrar
            </button>
          </div>
        </div>
      )}

      {/* Edit mode */}
      {editing && (
        <div className="p-3 space-y-3">
          <input
            type="text"
            value={form.phase_name}
            onChange={(e) => setForm({ ...form, phase_name: e.target.value })}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-500"
          />
          <div className="grid grid-cols-3 gap-2">
            {(['points_winner', 'points_goal_diff', 'points_exact_score'] as const).map((field, i) => (
              <div key={field}>
                <label className="text-slate-400 text-xs block mb-1">
                  {['Ganador', 'Dif. goles', 'Exacto'][i]}
                </label>
                <input
                  type="number" min={0}
                  value={form[field]}
                  onChange={(e) => setForm({ ...form, [field]: Number(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:border-green-500"
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={saveEdit}
              disabled={update.isPending}
              className="flex-1 bg-green-500 hover:bg-green-600 disabled:bg-slate-600 text-white text-sm font-semibold py-1.5 rounded-lg transition-colors"
            >
              {update.isPending ? 'Guardando...' : 'Guardar'}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-4 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm py-1.5 rounded-lg transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export function Settings() {
  const { data: phases, isLoading } = usePhaseConfigs()

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24 space-y-4">
      <h1 className="text-white text-xl font-bold mb-6">Ajustes</h1>

      <div>
        <h2 className="text-slate-300 font-semibold mb-3">Fases de la Penca</h2>
        {isLoading && <div className="bg-slate-800 rounded-xl h-20 animate-pulse" />}
        {!isLoading && phases?.map((phase) => (
          <PhaseCard key={phase.id} phase={phase} />
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
