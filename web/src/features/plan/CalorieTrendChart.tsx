import { AreaChart } from '@tremor/react'
import { Card } from '@/components/Card'
import type { DayPlan } from '@/api/types'

interface CalorieTrendChartProps {
  days: DayPlan[]
}

/** Recharts/Tremor read numeric values off this key; the axis label comes from `index` below. */
const CALORIES_KEY = 'Calories'

export function CalorieTrendChart({ days }: CalorieTrendChartProps) {
  if (days.length === 0) return null

  const data = days.map((d) => ({ day: d.day, [CALORIES_KEY]: d.total_calories }))

  return (
    <Card className="mb-6">
      <h2 className="text-lg font-semibold mb-3">Calories this week</h2>
      <AreaChart
        className="h-48"
        data={data}
        index="day"
        categories={[CALORIES_KEY]}
        colors={['var(--color-chart-1)']}
        valueFormatter={(v: number) => `${v} cal`}
        showLegend={false}
        showAnimation={false}
      />
    </Card>
  )
}
