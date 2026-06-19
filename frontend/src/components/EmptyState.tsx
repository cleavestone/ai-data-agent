const EXAMPLES = [
  'How many customers do we have?',
  'Revenue by country — top 10',
  'Monthly revenue trend',
  'Best selling products',
  'Which customer tier drives most revenue?',
  'Orders by status breakdown',
]

interface EmptyStateProps {
  onSelect: (question: string) => void
}

export function EmptyState({ onSelect }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 px-4 py-12">
      <div className="text-center space-y-2">
        <div className="font-mono text-accent text-sm tracking-widest uppercase mb-4">
          AI · Data · Agent
        </div>
        <h1 className="text-2xl font-semibold text-text">Ask your data anything</h1>
        <p className="text-muted text-sm max-w-sm">
          Natural language questions answered with charts and tables
        </p>
      </div>

      <div className="flex flex-wrap gap-2 justify-center max-w-xl">
        {EXAMPLES.map(q => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="px-3 py-2 rounded-lg bg-surface2 border border-border text-sm text-dim
                       hover:border-accent hover:text-text hover:bg-accent-dim
                       transition-all duration-150 cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
