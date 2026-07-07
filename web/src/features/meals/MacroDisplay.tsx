export function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/40 px-3 py-2 text-center">
      <div className="text-lg font-semibold text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

interface MacroBarProps {
  protein: number
  carbs: number
  fat: number
}

export function MacroBar({ protein, carbs, fat }: MacroBarProps) {
  const total = protein + carbs + fat
  const pct = (grams: number) => (total > 0 ? (grams / total) * 100 : 0)

  const segments = [
    { key: 'protein', grams: protein, color: 'bg-chart-1' },
    { key: 'carbs', grams: carbs, color: 'bg-chart-3' },
    { key: 'fat', grams: fat, color: 'bg-chart-5' },
  ] as const

  const label = `Protein ${protein}g, Carbs ${carbs}g, Fat ${fat}g`

  return (
    <div>
      <div
        role="img"
        aria-label={label}
        className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted"
      >
        {segments.map((segment) => (
          <div
            key={segment.key}
            data-testid={`macro-segment-${segment.key}`}
            className={segment.color}
            style={{ width: `${pct(segment.grams)}%` }}
          />
        ))}
      </div>
      <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
        {segments.map((segment) => (
          <span key={segment.key} className="flex items-center gap-1 capitalize">
            <span className={`inline-block h-2 w-2 rounded-full ${segment.color}`} />
            {segment.key} {segment.grams}g
          </span>
        ))}
      </div>
    </div>
  )
}
