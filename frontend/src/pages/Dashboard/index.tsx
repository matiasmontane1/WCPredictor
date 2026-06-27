import { useTodayMatches } from '../../api/client'
import { MatchCard } from '../../components/MatchCard'
import { NextSyncWidget } from '../../components/NextSyncWidget'

export function Dashboard() {
  const { data: matches, isLoading, error } = useTodayMatches()

  return (
    <div className="max-w-lg mx-auto px-4 pt-6 pb-24">
      <div className="mb-2">
        <h1 className="text-white text-xl font-bold">Partidos de Hoy</h1>
      </div>
      <div className="mb-6">
        <NextSyncWidget />
      </div>

      {new Date() <= new Date('2026-06-22T23:59:59') && (
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-xl p-4 mb-2 text-sm text-blue-200 space-y-1">
          <div className="font-semibold text-blue-300">Actualización del modelo</div>
          <p className="text-blue-200/80 leading-snug">
            Actualmente el modelo está priorizando las cuotas de apuestas, por lo que las sugerencias de hoy podrían apuntar a marcadores con menos goles. A medida que se evalúen más partidos, los pesos se irán ajustando y las sugerencias serán cada vez más precisas.
          </p>
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-slate-800 rounded-xl h-36 animate-pulse" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-xl p-4 text-red-300 text-sm text-center">
          Error al cargar los partidos. Verificá que el servidor esté corriendo.
        </div>
      )}

      {!isLoading && !error && matches?.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">⚽</div>
          <p className="font-medium">No hay partidos hoy</p>
          <p className="text-sm mt-1">Sincronizá para actualizar</p>
        </div>
      )}

      {!isLoading && !error && matches && matches.length > 0 && (
        <div className="space-y-3">
          {matches
            .filter((m) => !['finished', 'awarded'].includes(m.status.toLowerCase()))
            .map((match) => (
              <MatchCard key={match.id} match={match} />
            ))}
        </div>
      )}
    </div>
  )
}
