import { QueryClient, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

async function api<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'API error')
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// --- Types ---
export interface PhaseConfig {
  id: number
  phase_name: string
  points_winner: number
  points_goal_diff: number
  points_exact_score: number
  is_active: boolean
  created_at: string
}

export interface SuggestionOut {
  score: string
  probability: number
  ev: number
}

export interface MatchSummary {
  id: number
  match_date: string
  kickoff_time?: string
  home_team: string
  away_team: string
  phase?: string
  status: string
  has_metrics: boolean
  suggestions?: {
    conservative?: SuggestionOut
    aggressive?: SuggestionOut
  }
  actual_home_goals?: number
  actual_away_goals?: number
}

export interface ScoreDistributionItem {
  score: string
  probability: number
  ev: number
  rank: number
}

export interface MatchDetail extends MatchSummary {
  metrics?: {
    xg_home?: number
    xg_away?: number
    implied_prob_home?: number
    implied_prob_draw?: number
    implied_prob_away?: number
  }
  score_distribution: ScoreDistributionItem[]
}

export interface ModelWeights {
  weight_xg: number
  weight_market: number
  matches_evaluated: number
  last_updated_at?: string
}

export interface ValidateOut {
  score: string
  probability: number
  ev: number
  rank_among_computed: number
  total_scores_computed: number
  verdict: 'top_pick' | 'above_average' | 'below_average'
}

// --- Phase Config Hooks ---
export function usePhaseConfigs() {
  return useQuery<PhaseConfig[]>({
    queryKey: ['phases'],
    queryFn: () => api('/config/phase'),
  })
}

export function useCreatePhase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { phase_name: string; points_winner: number; points_goal_diff: number; points_exact_score: number }) =>
      api<PhaseConfig>('/config/phase', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['phases'] }),
  })
}

export function useActivatePhase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      api<PhaseConfig>(`/config/phase/${id}/activate`, { method: 'PUT' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['phases'] })
      qc.invalidateQueries({ queryKey: ['matches'] })
    },
  })
}

export function useDeletePhase() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api(`/config/phase/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['phases'] }),
  })
}

// --- Sync Hooks ---
export function useTriggerSync() {
  return useMutation({
    mutationFn: () => api<{ job_id: string; status: string; message: string }>('/sync', { method: 'POST', body: '{}' }),
  })
}

export function useSyncStatus(jobId: string | null) {
  return useQuery({
    queryKey: ['sync-status', jobId],
    queryFn: () => api<{ job_id: string; status: string; results?: Record<string, unknown> }>(`/sync/status/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (q) => {
      const status = q.state.data?.status
      return status === 'running' || status === 'started' ? 3000 : false
    },
  })
}

// --- Match Hooks ---
export function useTodayMatches() {
  return useQuery<MatchSummary[]>({
    queryKey: ['matches', 'today'],
    queryFn: () => api('/matches/today'),
    refetchOnWindowFocus: true,
  })
}

export function useAllMatches() {
  return useQuery<MatchSummary[]>({
    queryKey: ['matches', 'all'],
    queryFn: () => api('/matches/all'),
  })
}

export function useMatchDetail(matchId: number) {
  return useQuery<MatchDetail>({
    queryKey: ['match', matchId],
    queryFn: () => api(`/matches/${matchId}`),
    enabled: !!matchId,
  })
}

export function useYesterdayMatches() {
  return useQuery<MatchSummary[]>({
    queryKey: ['matches', 'yesterday'],
    queryFn: () => api('/matches/yesterday'),
  })
}

// --- Results Hook ---
export function useSubmitResult() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ matchId, goals_home, goals_away }: { matchId: number; goals_home: number; goals_away: number }) =>
      api(`/matches/${matchId}/result`, { method: 'POST', body: JSON.stringify({ goals_home, goals_away }) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['matches'] })
      qc.invalidateQueries({ queryKey: ['weights'] })
    },
  })
}

// --- Validate Hook ---
export function useValidateScore() {
  return useMutation({
    mutationFn: (data: { match_id: number; goals_home: number; goals_away: number }) =>
      api<ValidateOut>('/validate', { method: 'POST', body: JSON.stringify(data) }),
  })
}

// --- Weights Hook ---
export function useModelWeights() {
  return useQuery<ModelWeights>({
    queryKey: ['weights'],
    queryFn: () => api('/weights'),
  })
}
