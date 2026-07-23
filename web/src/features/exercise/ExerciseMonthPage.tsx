import { Link, useNavigate } from 'react-router-dom'
import { Card } from '@/components/Card'
import { Button } from '@/components/ui/button'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import { ApiError } from '@/api/client'
import { getTodayInEST, getCurrentWeekDates } from '@/features/exercise/dateUtils'
import { useExerciseMonth } from '@/features/exercise/hooks'
import {
  EXERCISE_TYPE_LABELS,
  EXERCISE_TYPE_ORDER,
  exerciseAccentVariants,
  exerciseSwatchVariants,
} from '@/features/exercise/exerciseColors'
import type { ExerciseDayPlan, ExerciseType } from '@/api/types'

const WEEKDAY_HEADERS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function currentMonth(): string {
  return getTodayInEST().slice(0, 7)
}

/** Monday-first weekday index (0 = Monday .. 6 = Sunday) for an ISO date. */
function mondayFirstWeekdayIndex(date: string): number {
  const sundayFirstIndex = new Date(`${date}T00:00:00`).getDay()
  return (sundayFirstIndex + 6) % 7
}

/** ISO date of the Monday that starts the week containing the given date. */
function mondayOfWeekContaining(date: string): string {
  return getCurrentWeekDates(date)[0].date
}

function typesPresent(day: ExerciseDayPlan): ExerciseType[] {
  const present = new Set(day.exercises.map((exercise) => exercise.type))
  return EXERCISE_TYPE_ORDER.filter((type) => present.has(type))
}

function dayBadge(day: ExerciseDayPlan): string | null {
  if (day.exercises.length === 0) return null
  return `${day.exercises.length} ex · ${day.total_calories} cal`
}

/** Single left-border accent color when exactly one exercise type is present,
 *  matching the weekly view's per-row accent (exerciseAccentVariants). Days
 *  with multiple types use colored dots instead (see typesPresent). */
function dayAccentClassName(day: ExerciseDayPlan): string {
  const types = typesPresent(day)
  return types.length === 1 ? exerciseAccentVariants({ type: types[0] }) : ''
}

function dateNumber(date: string): string {
  return String(Number(date.slice(8, 10)))
}

/** Pads a month's days into full 7-day weeks, Monday-first, for grid layout. */
function buildMonthGridCells(days: ExerciseDayPlan[]): (ExerciseDayPlan | null)[] {
  if (days.length === 0) return []
  const leadingBlanks = mondayFirstWeekdayIndex(days[0].date)
  const cells: (ExerciseDayPlan | null)[] = [...Array(leadingBlanks).fill(null), ...days]
  while (cells.length % 7 !== 0) cells.push(null)
  return cells
}

export function ExerciseMonthPage() {
  const month = currentMonth()
  const today = getTodayInEST()
  const navigate = useNavigate()

  const { data, isLoading, isError, error } = useExerciseMonth(month)

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner message={error instanceof ApiError ? error.message : 'Failed to load exercise month'} />
    )

  const cells = buildMonthGridCells(data?.days ?? [])

  function handleDayClick(day: ExerciseDayPlan) {
    navigate(`/exercise?week_start=${mondayOfWeekContaining(day.date)}`)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold">{month}</h1>
        <Link to="/exercise" className="text-sm text-primary hover:underline">
          Week view
        </Link>
      </div>

      <ul className="flex gap-3 flex-wrap mb-3" aria-label="Exercise type legend">
        {EXERCISE_TYPE_ORDER.map((type) => (
          <li key={type} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className={exerciseSwatchVariants({ type })} aria-hidden="true" />
            {EXERCISE_TYPE_LABELS[type]}
          </li>
        ))}
      </ul>

      <div className="grid grid-cols-7 gap-2 mb-2 text-xs text-muted-foreground text-center">
        {WEEKDAY_HEADERS.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-2" role="grid" aria-label={`Exercises for ${month}`}>
        {cells.map((day, index) =>
          day ? (
            <Card key={day.date} className={dayAccentClassName(day)}>
              <Button
                variant={day.date === today ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleDayClick(day)}
              >
                {dateNumber(day.date)}
              </Button>
              {dayBadge(day) && (
                <p className="text-xs text-muted-foreground mt-1 text-center">{dayBadge(day)}</p>
              )}
              {typesPresent(day).length > 1 && (
                <div className="flex gap-1 justify-center mt-1">
                  {typesPresent(day).map((type) => (
                    <span key={type} className={exerciseSwatchVariants({ type })} aria-hidden="true" />
                  ))}
                </div>
              )}
            </Card>
          ) : (
            <div key={`blank-${index}`} />
          )
        )}
      </div>
    </div>
  )
}
