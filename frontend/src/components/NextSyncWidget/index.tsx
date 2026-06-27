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

function ClockIcon() {
  return (
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
  )
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

  return (
    <div className="flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5">
      <ClockIcon />
      <span className="text-xs text-slate-500 whitespace-nowrap">Se actualiza a las:</span>
      {times.length === 0 ? (
        <span className="text-xs text-slate-400 font-medium whitespace-nowrap">—</span>
      ) : (
        <div className="flex items-center gap-1.5">
          {times.map((t, i) => (
            <span key={t} className="flex items-center gap-1.5">
              {i > 0 && <span className="text-slate-700">·</span>}
              <span className={`text-xs font-medium whitespace-nowrap ${i === 0 ? 'text-slate-300' : 'text-slate-500'}`}>
                {formatTime(t)}
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
