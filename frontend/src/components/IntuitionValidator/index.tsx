import { useEffect, useRef, useState } from 'react'
import { useValidateScore, type ValidateOut } from '../../api/client'

interface Props {
  matchId: number
}

const SCORE_REGEX = /^(\d)-(\d)$/

const verdictConfig = {
  top_pick: { label: 'Top Pick', className: 'bg-green-500 text-white' },
  above_average: { label: 'Por arriba del promedio', className: 'bg-yellow-500 text-black' },
  below_average: { label: 'Por debajo del promedio', className: 'bg-slate-600 text-slate-200' },
}

export function IntuitionValidator({ matchId }: Props) {
  const [input, setInput] = useState('')
  const [result, setResult] = useState<ValidateOut | null>(null)
  const validate = useValidateScore()
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setResult(null)
    if (!input) return

    const match = input.match(SCORE_REGEX)
    if (!match) return

    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      validate.mutate(
        {
          match_id: matchId,
          goals_home: parseInt(match[1]),
          goals_away: parseInt(match[2]),
        },
        { onSuccess: setResult, onError: () => setResult(null) }
      )
    }, 400)

    return () => { if (timer.current) clearTimeout(timer.current) }
  }, [input, matchId])

  const isValidFormat = SCORE_REGEX.test(input)

  return (
    <div className="bg-slate-800 rounded-xl p-4">
      <h3 className="text-slate-300 font-semibold mb-3">¿Tenés un presentimiento?</h3>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ej: 2-1"
        maxLength={3}
        className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-3 text-center text-xl font-mono focus:outline-none focus:border-green-500 placeholder-slate-500"
      />
      {input && !isValidFormat && (
        <p className="text-slate-500 text-xs text-center mt-2">Formato: goles_local-goles_visitante (ej: 2-1)</p>
      )}
      {validate.isPending && (
        <div className="text-center text-slate-400 text-sm mt-3">Calculando...</div>
      )}
      {result && (
        <div className="mt-3 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-sm">Probabilidad</span>
            <span className="text-white font-bold">{(result.probability * 100).toFixed(2)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-sm">Valor Esperado</span>
            <span className="text-white font-bold">{result.ev.toFixed(2)} pts</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-sm">Ranking</span>
            <span className="text-white font-bold">#{result.rank_among_computed} de {result.total_scores_computed}</span>
          </div>
          <div className="mt-2 text-center">
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${verdictConfig[result.verdict].className}`}>
              {verdictConfig[result.verdict].label}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
