import { useSyncSchedule } from '../../api/client'

const CHILE_TZ = 'America/Santiago'

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('es-CL', {
    timeZone: CHILE_TZ,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function NextSyncWidget() {
  const { data, isLoading } = useSyncSchedule()

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2 text-slate-500 text-sm animate-pulse">
        <div className="h-3 w-20 bg-slate-700 rounded" />
      </div>
    )
  }

  const times = data?.scheduled ?? []
  const next = data?.next ?? null

  return (
    <div className="flex flex-col items-end gap-0.5">
      <div className="flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5">
        <svg
          className="h-3.5 w-3.5 text-slate-400 shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <circle cx="12" cy="12" r="10" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2" />
        </svg>
        <span className="text-xs text-slate-400 font-medium whitespace-nowrap">
          {next ? `Sync ${formatTime(next)}` : 'Sin más syncs hoy'}
        </span>
      </div>

      {times.length > 1 && (
        <div className="flex items-center gap-1 px-1">
          {times.map((t) => (
            <span key={t} className="text-[10px] text-slate-600">
              {formatTime(t)}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
