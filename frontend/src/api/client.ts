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
  phase_id?: number
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
  actual_home_goals?: number | null
  actual_away_goals?: number | null
  suggestions?: {
    conservative?: SuggestionOut
    aggressive?: SuggestionOut
  }
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
  prob_home_win?: number
  prob_draw?: number
  prob_away_win?: number
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

// Fixed phase definitions — mirror of backend FIXED_PHASES in phase_config.py
export const FIXED_PHASES: PhaseConfig[] = [
  { id: 1, phase_name: 'Fase de grupos', points_winner: 2, points_goal_diff: 3, points_exact_score: 5, is_active: false, created_at: '' },
  { id: 2, phase_name: '16avos y 8avos', points_winner: 3, points_goal_diff: 5, points_exact_score: 8, is_active: false, created_at: '' },
  { id: 3, phase_name: '4tos en adelante', points_winner: 5, points_goal_diff: 7, points_exact_score: 11, is_active: false, created_at: '' },
]

// --- Phase Config Hooks ---
export function useActivePhase() {
  return useQuery<PhaseConfig>({
    queryKey: ['phases', 'active'],
    queryFn: () => api('/config/phase/active'),
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

export function usePastMatches() {
  return useQuery<MatchSummary[]>({
    queryKey: ['matches', 'past'],
    queryFn: () => api('/matches/past'),
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

// --- WC Stats Hook ---
export interface ScorelineItem {
  score: string
  count: number
  pct: number
}

export interface TotalGoalsItem {
  goals: number
  count: number
  pct: number
}

export interface LastMatchItem {
  home_team: string
  away_team: string
  score: string
  kickoff_time?: string
}

export interface WCStats {
  total_matches: number
  top_scorelines: ScorelineItem[]
  margin_distribution: Record<string, number>
  total_goals_distribution: TotalGoalsItem[]
  btts_percentage: number
  last_match?: LastMatchItem
}

export function useWCStats() {
  return useQuery<WCStats>({
    queryKey: ['stats', 'wc'],
    queryFn: () => api('/stats/wc'),
  })
}

// --- Weights Hook ---
export function useModelWeights() {
  return useQuery<ModelWeights>({
    queryKey: ['weights'],
    queryFn: () => api('/weights'),
  })
}

export function useResetWeights() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api<ModelWeights>('/weights/reset', { method: 'POST', body: '{}' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['weights'] }),
  })
}
