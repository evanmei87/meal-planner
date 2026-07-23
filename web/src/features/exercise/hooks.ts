import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type {
  AddExerciseRequest,
  PresetExercise,
  ReorderExercisesRequest,
  UpdateExerciseRequest,
} from '@/api/types'

export function useExerciseWeek(weekStart: string) {
  return useQuery({ queryKey: ['exercises', weekStart], queryFn: () => api.exercises.getWeek(weekStart) })
}

export function useAddExercise(weekStart: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: AddExerciseRequest) => api.exercises.add(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exercises', weekStart] }),
  })
}

export function useUpdateExercise(weekStart: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, req }: { id: string; req: UpdateExerciseRequest }) => api.exercises.update(id, req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exercises', weekStart] }),
  })
}

export function useReorderExercises(weekStart: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: ReorderExercisesRequest) => api.exercises.reorder(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exercises', weekStart] }),
  })
}

export function useDeleteExercise(weekStart: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.exercises.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exercises', weekStart] }),
  })
}

export function useSavePreset() {
  return useMutation({
    mutationFn: ({ dayName, exercises }: { dayName: string; exercises: PresetExercise[] }) =>
      api.exercisePresets.save(dayName, exercises),
  })
}
