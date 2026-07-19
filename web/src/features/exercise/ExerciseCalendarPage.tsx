import { useState } from 'react'
import { Card } from '@/components/Card'
import { Button } from '@/components/ui/button'
import { getTodayInEST, getCurrentWeekDates } from '@/features/exercise/dateUtils'

function formatShortDate(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

export function ExerciseCalendarPage() {
  const today = getTodayInEST()
  const week = getCurrentWeekDates()
  const [selectedDate, setSelectedDate] = useState(today)

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {week.map((day) => (
          <Card key={day.date}>
            <Button
              variant={day.date === today ? 'default' : 'ghost'}
              onClick={() => setSelectedDate(day.date)}
            >
              {day.dayName.slice(0, 3)}, {formatShortDate(day.date)}
            </Button>
          </Card>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">Exercises for {selectedDate}</p>
    </div>
  )
}
