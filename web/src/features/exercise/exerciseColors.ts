import { cva } from 'class-variance-authority'
import type { ExerciseType } from '@/api/types'

/**
 * Colors for each exercise type, sourced from the `--color-exercise-*` design
 * tokens in index.css (not raw Tailwind palette classes) so the palette stays
 * consistent with the app's token system, including future dark mode.
 */

export const EXERCISE_TYPE_ORDER: ExerciseType[] = [
  'running',
  'walking',
  'biking',
  'swimming',
  'strength',
]

export const EXERCISE_TYPE_LABELS: Record<ExerciseType, string> = {
  running: 'Running',
  walking: 'Walking',
  biking: 'Biking',
  swimming: 'Swimming',
  strength: 'Strength',
}

/** Left-border + background accent applied to an exercise row. */
export const exerciseAccentVariants = cva('border-l-4', {
  variants: {
    type: {
      running: 'border-exercise-running bg-exercise-running-subtle',
      walking: 'border-exercise-walking bg-exercise-walking-subtle',
      biking: 'border-exercise-biking bg-exercise-biking-subtle',
      swimming: 'border-exercise-swimming bg-exercise-swimming-subtle',
      strength: 'border-exercise-strength bg-exercise-strength-subtle',
    } satisfies Record<ExerciseType, string>,
  },
})

/** Solid color swatch used by the legend. */
export const exerciseSwatchVariants = cva('inline-block size-3 rounded-full', {
  variants: {
    type: {
      running: 'bg-exercise-running',
      walking: 'bg-exercise-walking',
      biking: 'bg-exercise-biking',
      swimming: 'bg-exercise-swimming',
      strength: 'bg-exercise-strength',
    } satisfies Record<ExerciseType, string>,
  },
})
