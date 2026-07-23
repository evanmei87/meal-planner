import { useState } from 'react'
import { Card } from '@/components/Card'
import { Button } from '@/components/ui/button'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import { ApiError } from '@/api/client'
import { getTodayInEST, getCurrentWeekDates } from '@/features/exercise/dateUtils'
import { useAddExercise, useDeleteExercise, useExerciseWeek, useUpdateExercise } from '@/features/exercise/hooks'
import type { ExerciseDayPlan, ExerciseItem } from '@/api/types'

const inputClassName =
  'border rounded-md px-2 py-1 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring'

function formatShortDate(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

function dayBadge(day: ExerciseDayPlan | undefined): string | null {
  if (!day || day.exercises.length === 0) return null
  const count = day.exercises.length
  return `${count} run${count === 1 ? '' : 's'} · ${day.total_calories} cal`
}

export function ExerciseCalendarPage() {
  const today = getTodayInEST()
  const week = getCurrentWeekDates()
  const weekStart = week[0].date
  const [selectedDate, setSelectedDate] = useState(today)
  const [distanceMiles, setDistanceMiles] = useState('')
  const [durationMinutes, setDurationMinutes] = useState('')
  const [notes, setNotes] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)

  const { data, isLoading, isError, error } = useExerciseWeek(weekStart)
  const addExercise = useAddExercise(weekStart)
  const updateExercise = useUpdateExercise(weekStart)
  const deleteExercise = useDeleteExercise(weekStart)

  const selectedDay = data?.days.find((d) => d.date === selectedDate)

  function resetForm() {
    setDistanceMiles('')
    setDurationMinutes('')
    setNotes('')
    setEditingId(null)
  }

  function handleEditClick(exercise: ExerciseItem) {
    setEditingId(exercise.id)
    setDistanceMiles(String(exercise.distance_miles))
    setDurationMinutes(String(exercise.duration_minutes))
    setNotes(exercise.notes ?? '')
  }

  function handleRemoveClick(exercise: ExerciseItem) {
    if (!window.confirm('Remove this exercise?')) return
    deleteExercise.mutate(exercise.id)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const req = {
      distance_miles: parseFloat(distanceMiles),
      duration_minutes: parseFloat(durationMinutes),
      notes: notes.trim() || undefined,
    }

    if (editingId) {
      updateExercise.mutate({ id: editingId, req }, { onSuccess: resetForm })
    } else {
      addExercise.mutate({ date: selectedDate, ...req }, { onSuccess: resetForm })
    }
  }

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load exercises'}
      />
    )

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {week.map((day) => {
          const badge = dayBadge(data?.days.find((d) => d.date === day.date))
          return (
            <Card key={day.date}>
              <Button
                variant={day.date === today ? 'default' : 'ghost'}
                onClick={() => setSelectedDate(day.date)}
              >
                {day.dayName.slice(0, 3)}, {formatShortDate(day.date)}
              </Button>
              {badge && <p className="text-xs text-muted-foreground mt-1 text-center">{badge}</p>}
            </Card>
          )
        })}
      </div>

      <Card>
        <p className="text-sm text-muted-foreground mb-3">Exercises for {selectedDate}</p>

        {!selectedDay || selectedDay.exercises.length === 0 ? (
          <p className="text-sm text-muted-foreground mb-4">No exercises logged for this day.</p>
        ) : (
          <ul className="mb-4 space-y-1">
            {selectedDay.exercises.map((exercise) => (
              <li key={exercise.id} className="text-sm flex items-center gap-2">
                <span>
                  {exercise.distance_miles} mi · {exercise.duration_minutes} min · {exercise.calories} cal
                </span>
                {exercise.notes && <span className="text-muted-foreground"> — {exercise.notes}</span>}
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() => handleEditClick(exercise)}
                >
                  Edit
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  size="xs"
                  onClick={() => handleRemoveClick(exercise)}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2 flex-wrap items-end">
          <div>
            <label htmlFor="exercise-distance" className="block text-xs text-muted-foreground mb-1">
              Distance (mi)
            </label>
            <input
              id="exercise-distance"
              type="number"
              step="0.1"
              min="0"
              required
              value={distanceMiles}
              onChange={(e) => setDistanceMiles(e.target.value)}
              className={inputClassName}
            />
          </div>
          <div>
            <label htmlFor="exercise-duration" className="block text-xs text-muted-foreground mb-1">
              Duration (min)
            </label>
            <input
              id="exercise-duration"
              type="number"
              step="1"
              min="0"
              required
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(e.target.value)}
              className={inputClassName}
            />
          </div>
          <div>
            <label htmlFor="exercise-notes" className="block text-xs text-muted-foreground mb-1">
              Notes (optional)
            </label>
            <input
              id="exercise-notes"
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className={inputClassName}
            />
          </div>
          <Button type="submit" disabled={addExercise.isPending || updateExercise.isPending}>
            {editingId
              ? updateExercise.isPending
                ? 'Saving…'
                : 'Save Changes'
              : addExercise.isPending
                ? 'Adding…'
                : 'Add Exercise'}
          </Button>
          {editingId && (
            <Button type="button" variant="outline" onClick={resetForm}>
              Cancel
            </Button>
          )}
        </form>

        {addExercise.isError && <ErrorBanner message="Failed to add exercise" />}
        {updateExercise.isError && <ErrorBanner message="Failed to update exercise" />}
        {deleteExercise.isError && <ErrorBanner message="Failed to remove exercise" />}
      </Card>
    </div>
  )
}
