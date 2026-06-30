import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

const BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

async function adminApi<T>(path: string, password: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', 'X-Admin-Password': password },
  })
  if (!res.ok) throw new Error('Unauthorized')
  return res.json()
}

interface PhaseCalibration {
  phase: string
  total_matches: number
  avg_brier_xg: number | null
  avg_brier_market: number | null
  avg_prob_draw_predicted: number | null
  draw_rate_actual: number | null
  draws_actual: number
}

interface LogEntry {
  match_id: number
  match: string
  phase: string | null
  actual_score: string
  prob_home: number | null
  prob_draw: number | null
  prob_away: number | null
  brier_xg: number | null
  brier_market: number | null
  evaluated_at: string | null
}

interface Weights {
  weight_xg: number
  weight_market: number
  matches_evaluated: number
  last_updated_at: string | null
}

function pct(v: number | null) {
  if (v === null) return '—'
  return `${(v * 100).toFixed(1)}%`
}

function num(v: number | null, decimals = 3) {
  if (v === null) return '—'
  return v.toFixed(decimals)
}

function BrierCell({ value }: { value: number | null }) {
  if (value === null) return <td className="px-3 py-2 text-slate-500">—</td>
  const color = value < 0.4 ? 'text-green-400' : value < 0.6 ? 'text-yellow-400' : 'text-red-400'
  return <td className={`px-3 py-2 font-mono ${color}`}>{value.toFixed(4)}</td>
}

export function Admin() {
  const [password, setPassword] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [input, setInput] = useState('')

  const calibrationQ = useQuery({
    queryKey: ['admin', 'calibration', submitted],
    queryFn: () => adminApi<{ phases: PhaseCalibration[] }>('/admin/calibration', submitted),
    enabled: !!submitted,
    retry: false,
  })

  const logsQ = useQuery({
    queryKey: ['admin', 'logs', submitted],
    queryFn: () => adminApi<{ logs: LogEntry[] }>('/admin/logs', submitted),
    enabled: !!submitted,
    retry: false,
  })

  const weightsQ = useQuery({
    queryKey: ['admin', 'weights', submitted],
    queryFn: () => adminApi<Weights>('/admin/weights', submitted),
    enabled: !!submitted,
    retry: false,
  })

  const isUnauthorized =
    calibrationQ.isError || logsQ.isError || weightsQ.isError

  if (!submitted) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center pb-20">
        <div className="bg-slate-800 rounded-xl p-8 w-80 space-y-4">
          <h1 className="text-white text-xl font-bold text-center">Admin</h1>
          <input
            type="password"
            placeholder="Contraseña"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && setSubmitted(input)}
            className="w-full bg-slate-700 text-white rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={() => setSubmitted(input)}
            className="w-full bg-green-600 hover:bg-green-500 text-white font-semibold rounded-lg py-2 transition-colors"
          >
            Entrar
          </button>
        </div>
      </div>
    )
  }

  if (isUnauthorized) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center pb-20">
        <div className="bg-slate-800 rounded-xl p-8 w-80 space-y-4 text-center">
          <p className="text-red-400 font-semibold">Contraseña incorrecta</p>
          <button
            onClick={() => { setSubmitted(''); setInput('') }}
            className="text-slate-400 text-sm underline"
          >
            Volver
          </button>
        </div>
      </div>
    )
  }

  const phases = calibrationQ.data?.phases ?? []
  const logs = logsQ.data?.logs ?? []
  const weights = weightsQ.data

  return (
    <div className="min-h-screen bg-slate-900 text-white pb-24 px-4 pt-6 max-w-3xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Panel Admin</h1>

      {/* Weights */}
      <section className="bg-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-3 text-slate-200">Pesos del modelo</h2>
        {weights ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-slate-400 text-xs mb-1">xG</p>
              <p className="text-2xl font-bold text-green-400">{pct(weights.weight_xg)}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs mb-1">Mercado</p>
              <p className="text-2xl font-bold text-blue-400">{pct(weights.weight_market)}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs mb-1">Partidos evaluados</p>
              <p className="text-lg font-semibold">{weights.matches_evaluated}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs mb-1">Última actualización</p>
              <p className="text-sm text-slate-300">
                {weights.last_updated_at ? new Date(weights.last_updated_at).toLocaleString('es-CL') : '—'}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-slate-400 text-sm">Cargando...</p>
        )}
      </section>

      {/* Calibration by phase */}
      <section className="bg-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-3 text-slate-200">Calibración por fase</h2>
        {phases.length === 0 ? (
          <p className="text-slate-400 text-sm">Sin datos aún.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-xs border-b border-slate-700">
                  <th className="px-3 py-2 text-left">Fase</th>
                  <th className="px-3 py-2 text-right">N</th>
                  <th className="px-3 py-2 text-right">Brier xG</th>
                  <th className="px-3 py-2 text-right">Brier Mkt</th>
                  <th className="px-3 py-2 text-right">P(X) pred.</th>
                  <th className="px-3 py-2 text-right">P(X) real</th>
                </tr>
              </thead>
              <tbody>
                {phases.map((p) => (
                  <tr key={p.phase} className="border-b border-slate-700/50">
                    <td className="px-3 py-2 text-slate-300 max-w-[120px] truncate">{p.phase}</td>
                    <td className="px-3 py-2 text-right text-slate-300">{p.total_matches}</td>
                    <BrierCell value={p.avg_brier_xg} />
                    <BrierCell value={p.avg_brier_market} />
                    <td className="px-3 py-2 text-right font-mono text-slate-300">{pct(p.avg_prob_draw_predicted)}</td>
                    <td className={`px-3 py-2 text-right font-mono font-semibold ${
                      p.avg_prob_draw_predicted !== null && p.draw_rate_actual !== null &&
                      p.draw_rate_actual - p.avg_prob_draw_predicted > 0.15
                        ? 'text-red-400'
                        : 'text-slate-300'
                    }`}>
                      {pct(p.draw_rate_actual)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-slate-500 text-xs mt-3">
          P(X) en rojo = modelo subestima empates por más de 15pp
        </p>
      </section>

      {/* Recent logs */}
      <section className="bg-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold mb-3 text-slate-200">Últimos partidos evaluados</h2>
        {logs.length === 0 ? (
          <p className="text-slate-400 text-sm">Sin registros aún.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-xs border-b border-slate-700">
                  <th className="px-3 py-2 text-left">Partido</th>
                  <th className="px-3 py-2 text-right">Score</th>
                  <th className="px-3 py-2 text-right">P(1)</th>
                  <th className="px-3 py-2 text-right">P(X)</th>
                  <th className="px-3 py-2 text-right">P(2)</th>
                  <th className="px-3 py-2 text-right">B.xG</th>
                  <th className="px-3 py-2 text-right">B.Mkt</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.match_id} className="border-b border-slate-700/50">
                    <td className="px-3 py-2 text-slate-300 max-w-[140px]">
                      <div className="truncate">{log.match}</div>
                      <div className="text-xs text-slate-500">{log.phase ?? '—'}</div>
                    </td>
                    <td className="px-3 py-2 text-right font-mono font-bold text-white">{log.actual_score}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-300">{num(log.prob_home)}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-300">{num(log.prob_draw)}</td>
                    <td className="px-3 py-2 text-right font-mono text-slate-300">{num(log.prob_away)}</td>
                    <BrierCell value={log.brier_xg} />
                    <BrierCell value={log.brier_market} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
