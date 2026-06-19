import { useEffect, useState } from 'react'

const STEPS = [
  'Reading schema...',
  'Writing SQL...',
  'Querying database...',
  'Analysing results...',
]

export function ThinkingCard() {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setStep(s => (s + 1) % STEPS.length), 1800)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="rounded-xl bg-surface border border-border p-4 space-y-3">
      <div className="flex gap-1.5 items-center">
        {[0, 1, 2].map(i => (
          <div
            key={i}
            className="w-2 h-2 rounded-full bg-accent"
            style={{ animation: `dotBounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
          />
        ))}
      </div>
      <p className="font-mono text-xs text-muted transition-all duration-300">
        {STEPS[step]}
      </p>
    </div>
  )
}
