import { describe, expect, it } from 'vitest'
import { resolveDragEnd } from './ExerciseCalendarPage'
import type { ExerciseItem } from '@/api/types'

function exercise(id: string, order: number): ExerciseItem {
  return {
    id,
    type: 'running',
    distance_miles: 3,
    duration_minutes: 30,
    calories: 300,
    notes: null,
    order,
  }
}

describe('resolveDragEnd', () => {
  const exercises = [exercise('a', 0), exercise('b', 1), exercise('c', 2)]

  it('returns noop when dropped outside any droppable', () => {
    const decision = resolveDragEnd({ active: { id: 'a' }, over: null }, '2026-06-22', exercises)
    expect(decision).toEqual({ kind: 'noop' })
  })

  it('returns noop when dropped back on itself', () => {
    const decision = resolveDragEnd({ active: { id: 'a' }, over: { id: 'a' } }, '2026-06-22', exercises)
    expect(decision).toEqual({ kind: 'noop' })
  })

  it('returns a reorder decision with the new id order when dropped on another exercise in the same day', () => {
    const decision = resolveDragEnd({ active: { id: 'a' }, over: { id: 'c' } }, '2026-06-22', exercises)
    expect(decision).toEqual({ kind: 'reorder', date: '2026-06-22', orderedIds: ['b', 'c', 'a'] })
  })

  it('returns a move decision when dropped on a different day drop zone', () => {
    const decision = resolveDragEnd(
      { active: { id: 'a' }, over: { id: 'day:2026-06-24' } },
      '2026-06-22',
      exercises
    )
    expect(decision).toEqual({ kind: 'move', exerciseId: 'a', date: '2026-06-24' })
  })

  it('returns noop when dropped on the day drop zone for the currently selected day', () => {
    const decision = resolveDragEnd(
      { active: { id: 'a' }, over: { id: 'day:2026-06-22' } },
      '2026-06-22',
      exercises
    )
    expect(decision).toEqual({ kind: 'noop' })
  })

  it('returns noop when the dragged or target exercise id is unknown', () => {
    const decision = resolveDragEnd({ active: { id: 'unknown' }, over: { id: 'a' } }, '2026-06-22', exercises)
    expect(decision).toEqual({ kind: 'noop' })
  })
})
