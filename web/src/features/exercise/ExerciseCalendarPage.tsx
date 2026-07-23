import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  DndContext,
  PointerSensor,
  closestCenter,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card } from '@/components/Card'
import { Button } from '@/components/ui/button'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import { BlurFade } from '@/components/magicui/BlurFade'
import { ApiError } from '@/api/client'
import { getTodayInEST, getCurrentWeekDates } from '@/features/exercise/dateUtils'
import {
  useAddExercise,
  useDeleteExercise,
  useExerciseWeek,
  useReorderExercises,
  useSavePreset,
  useUpdateExercise,
} from '@/features/exercise/hooks'
import {
  EXERCISE_TYPE_LABELS,
  EXERCISE_TYPE_ORDER,
  exerciseAccentVariants,
  exerciseSwatchVariants,
} from '@/features/exercise/exerciseColors'
import type {
  AddExerciseRequest,
  ExerciseDayPlan,
  ExerciseItem,
  ExerciseType,
  PresetExercise,
  UpdateExerciseRequest,
} from '@/api/types'

const DAY_DROP_PREFIX = 'day:'

/** Prefixed so a day drop zone's id can never collide with an exercise id. */
function dayDropZoneId(date: string): string {
  return `${DAY_DROP_PREFIX}${date}`
}

export type DragEndDecision =
  | { kind: 'move'; exerciseId: string; date: string }
  | { kind: 'reorder'; date: string; orderedIds: string[] }
  | { kind: 'noop' }

/** The subset of a dnd-kit DragEndEvent that resolveDragEnd actually needs. */
export interface DragEndActiveOver {
  active: { id: string | number }
  over: { id: string | number } | null
}

/**
 * Pure decision logic for a drag-end event, kept free of hooks/mutations so
 * it can be unit tested directly instead of only through a full pointer-drag
 * simulation (unreliable in jsdom).
 */
export function resolveDragEnd(
  event: DragEndActiveOver,
  selectedDate: string,
  sortedExercises: ExerciseItem[]
): DragEndDecision {
  const { active, over } = event
  if (!over) return { kind: 'noop' }

  const activeId = String(active.id)
  const overId = String(over.id)

  if (overId.startsWith(DAY_DROP_PREFIX)) {
    const targetDate = overId.slice(DAY_DROP_PREFIX.length)
    if (targetDate === selectedDate) return { kind: 'noop' }
    return { kind: 'move', exerciseId: activeId, date: targetDate }
  }

  if (activeId === overId) return { kind: 'noop' }

  const oldIndex = sortedExercises.findIndex((e) => e.id === activeId)
  const newIndex = sortedExercises.findIndex((e) => e.id === overId)
  if (oldIndex === -1 || newIndex === -1) return { kind: 'noop' }

  const reordered = arrayMove(sortedExercises, oldIndex, newIndex)
  return { kind: 'reorder', date: selectedDate, orderedIds: reordered.map((e) => e.id) }
}

function toUpdateRequestFields(exercise: ExerciseItem): Omit<UpdateExerciseRequest, 'date' | 'order'> {
  return {
    type: exercise.type,
    distance_miles: exercise.distance_miles ?? undefined,
    duration_minutes: exercise.duration_minutes,
    sets: exercise.sets ?? undefined,
    reps: exercise.reps ?? undefined,
    notes: exercise.notes ?? undefined,
  }
}

/** Makes a day's card in the week strip a drop target for moving an exercise onto it. */
function DayDropZone({ date, children }: { date: string; children: React.ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id: dayDropZoneId(date) })
  return (
    <div ref={setNodeRef} className={isOver ? 'ring-2 ring-ring rounded-lg' : ''}>
      {children}
    </div>
  )
}

/** A draggable, reorderable exercise row. Only the handle carries the drag listeners, so Edit/Remove stay clickable. */
function SortableExerciseRow({ exercise, children }: { exercise: ExerciseItem; children: React.ReactNode }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: exercise.id })
  const style = { transform: CSS.Transform.toString(transform), transition }

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={`text-sm flex items-center gap-2 pl-2 py-1 ${exerciseAccentVariants({ type: exercise.type })} ${isDragging ? 'opacity-50' : ''}`}
    >
      <span
        {...attributes}
        {...listeners}
        aria-label="Drag to reorder or move to another day"
        className="cursor-grab text-muted-foreground px-1"
      >
        ⠿
      </span>
      {children}
    </li>
  )
}

const inputClassName =
  'border rounded-md px-2 py-1 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring'

const EXERCISE_TYPES: { value: ExerciseType; label: string }[] = EXERCISE_TYPE_ORDER.map((value) => ({
  value,
  label: EXERCISE_TYPE_LABELS[value],
}))

function usesSetsAndReps(type: ExerciseType): boolean {
  return type === 'strength'
}

function formatShortDate(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

function formatExerciseSummary(exercise: ExerciseItem): string {
  const activity = usesSetsAndReps(exercise.type)
    ? `${exercise.sets} sets × ${exercise.reps} reps`
    : `${exercise.distance_miles} mi`
  return `${activity} · ${exercise.duration_minutes} min · ${exercise.calories} cal`
}

function dayBadge(day: ExerciseDayPlan | undefined): string | null {
  if (!day || day.exercises.length === 0) return null
  const count = day.exercises.length
  return `${count} exercise${count === 1 ? '' : 's'} · ${day.total_calories} cal`
}

function toPresetExercise(exercise: ExerciseItem): PresetExercise {
  return {
    type: exercise.type,
    distance_miles: exercise.distance_miles ?? undefined,
    duration_minutes: exercise.duration_minutes,
    sets: exercise.sets ?? undefined,
    reps: exercise.reps ?? undefined,
    notes: exercise.notes ?? undefined,
  }
}

export function ExerciseCalendarPage() {
  const today = getTodayInEST()
  const week = getCurrentWeekDates()
  const weekStart = week[0].date
  const [selectedDate, setSelectedDate] = useState(today)
  const [exerciseType, setExerciseType] = useState<ExerciseType>('running')
  const [distanceMiles, setDistanceMiles] = useState('')
  const [durationMinutes, setDurationMinutes] = useState('')
  const [sets, setSets] = useState('')
  const [reps, setReps] = useState('')
  const [notes, setNotes] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [presetSaved, setPresetSaved] = useState(false)

  const { data, isLoading, isError, error } = useExerciseWeek(weekStart)
  const addExercise = useAddExercise(weekStart)
  const updateExercise = useUpdateExercise(weekStart)
  const deleteExercise = useDeleteExercise(weekStart)
  const reorderExercises = useReorderExercises(weekStart)
  const savePreset = useSavePreset()
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }))

  const selectedDay = data?.days.find((d) => d.date === selectedDate)
  const sortedExercises = selectedDay ? [...selectedDay.exercises].sort((a, b) => a.order - b.order) : []

  function handleDragEnd(event: DragEndEvent) {
    const decision = resolveDragEnd(event, selectedDate, sortedExercises)
    if (decision.kind === 'reorder') {
      reorderExercises.mutate({ date: decision.date, ordered_ids: decision.orderedIds })
    } else if (decision.kind === 'move') {
      const exercise = sortedExercises.find((e) => e.id === decision.exerciseId)
      if (!exercise) return
      updateExercise.mutate({
        id: decision.exerciseId,
        req: { ...toUpdateRequestFields(exercise), date: decision.date },
      })
    }
  }

  function resetForm() {
    setExerciseType('running')
    setDistanceMiles('')
    setDurationMinutes('')
    setSets('')
    setReps('')
    setNotes('')
    setEditingId(null)
  }

  function handleEditClick(exercise: ExerciseItem) {
    setEditingId(exercise.id)
    setExerciseType(exercise.type)
    setDistanceMiles(exercise.distance_miles != null ? String(exercise.distance_miles) : '')
    setDurationMinutes(String(exercise.duration_minutes))
    setSets(exercise.sets != null ? String(exercise.sets) : '')
    setReps(exercise.reps != null ? String(exercise.reps) : '')
    setNotes(exercise.notes ?? '')
  }

  function handleRemoveClick(exercise: ExerciseItem) {
    if (!window.confirm('Remove this exercise?')) return
    deleteExercise.mutate(exercise.id)
  }

  function handleSavePreset() {
    if (!selectedDay) return
    const exercises = selectedDay.exercises.map(toPresetExercise)
    savePreset.mutate(
      { dayName: selectedDay.day_name, exercises },
      {
        onSuccess: () => {
          setPresetSaved(true)
          setTimeout(() => setPresetSaved(false), 2000)
        },
      }
    )
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const req: Omit<AddExerciseRequest, 'date'> = {
      type: exerciseType,
      duration_minutes: parseFloat(durationMinutes),
      notes: notes.trim() || undefined,
      ...(usesSetsAndReps(exerciseType)
        ? { sets: parseInt(sets, 10), reps: parseInt(reps, 10) }
        : { distance_miles: parseFloat(distanceMiles) }),
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
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
    <div>
      <div className="flex justify-end mb-2">
        <Link to="/exercise/month" className="text-sm text-primary hover:underline">
          Month view
        </Link>
      </div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {week.map((day) => {
          const badge = dayBadge(data?.days.find((d) => d.date === day.date))
          return (
            <DayDropZone key={day.date} date={day.date}>
              <Card>
                <Button
                  variant={day.date === today ? 'default' : 'ghost'}
                  onClick={() => setSelectedDate(day.date)}
                >
                  {day.dayName.slice(0, 3)}, {formatShortDate(day.date)}
                </Button>
                {badge && <p className="text-xs text-muted-foreground mt-1 text-center">{badge}</p>}
              </Card>
            </DayDropZone>
          )
        })}
      </div>

      <Card>
        <p className="text-sm text-muted-foreground mb-3">Exercises for {selectedDate}</p>

        <ul className="flex gap-3 flex-wrap mb-3" aria-label="Exercise type legend">
          {EXERCISE_TYPE_ORDER.map((type) => (
            <li key={type} className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className={exerciseSwatchVariants({ type })} aria-hidden="true" />
              {EXERCISE_TYPE_LABELS[type]}
            </li>
          ))}
        </ul>

        <BlurFade transitionKey={selectedDate}>
          {!selectedDay || sortedExercises.length === 0 ? (
            <p className="text-sm text-muted-foreground mb-4">No exercises logged for this day.</p>
          ) : (
            <>
              <SortableContext items={sortedExercises.map((e) => e.id)} strategy={verticalListSortingStrategy}>
                <ul className="mb-3 space-y-1">
                  {sortedExercises.map((exercise) => (
                    <SortableExerciseRow key={exercise.id} exercise={exercise}>
                      <span>{formatExerciseSummary(exercise)}</span>
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
                    </SortableExerciseRow>
                  ))}
                </ul>
              </SortableContext>
              <div className="flex items-center gap-2 mb-4">
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={handleSavePreset}
                  disabled={savePreset.isPending}
                >
                  {savePreset.isPending ? 'Saving…' : 'Save to preset'}
                </Button>
                {presetSaved && <span className="text-xs text-muted-foreground">Saved!</span>}
              </div>
            </>
          )}
        </BlurFade>

        <form onSubmit={handleSubmit} className="flex gap-2 flex-wrap items-end">
          <div>
            <label htmlFor="exercise-type" className="block text-xs text-muted-foreground mb-1">
              Type
            </label>
            <select
              id="exercise-type"
              value={exerciseType}
              onChange={(e) => setExerciseType(e.target.value as ExerciseType)}
              className={inputClassName}
            >
              {EXERCISE_TYPES.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          {usesSetsAndReps(exerciseType) ? (
            <>
              <div>
                <label htmlFor="exercise-sets" className="block text-xs text-muted-foreground mb-1">
                  Sets
                </label>
                <input
                  id="exercise-sets"
                  type="number"
                  step="1"
                  min="0"
                  required
                  value={sets}
                  onChange={(e) => setSets(e.target.value)}
                  className={inputClassName}
                />
              </div>
              <div>
                <label htmlFor="exercise-reps" className="block text-xs text-muted-foreground mb-1">
                  Reps
                </label>
                <input
                  id="exercise-reps"
                  type="number"
                  step="1"
                  min="0"
                  required
                  value={reps}
                  onChange={(e) => setReps(e.target.value)}
                  className={inputClassName}
                />
              </div>
            </>
          ) : (
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
          )}
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
        {reorderExercises.isError && <ErrorBanner message="Failed to reorder exercises" />}
        {savePreset.isError && <ErrorBanner message="Failed to save preset" />}
      </Card>
    </div>
    </DndContext>
  )
}
