import { useEffect } from 'react'
import { useTriggerSync, useSyncStatus } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'
import { useQueryClient } from '@tanstack/react-query'

export function SyncButton() {
  const { syncJobId, setSyncJobId } = useAppStore()
  const trigger = useTriggerSync()
  const status = useSyncStatus(syncJobId)
  const qc = useQueryClient()

  const isRunning = status.data?.status === 'running' || status.data?.status === 'started' || trigger.isPending

  useEffect(() => {
    if (status.data?.status === 'completed') {
      qc.invalidateQueries({ queryKey: ['matches'] })
      setSyncJobId(null)
    }
  }, [status.data?.status, qc, setSyncJobId])

  function handleSync() {
    trigger.mutate(undefined, {
      onSuccess: (data) => setSyncJobId(data.job_id),
    })
  }

  return (
    <button
      onClick={handleSync}
      disabled={isRunning}
      className="flex items-center gap-2 bg-green-500 hover:bg-green-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold px-4 py-2 rounded-lg transition-colors"
    >
      {isRunning ? (
        <>
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Sincronizando...
        </>
      ) : (
        <>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Sincronizar Hoy
        </>
      )}
    </button>
  )
}
