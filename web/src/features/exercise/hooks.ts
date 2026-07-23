import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { AddExerciseRequest } from '@/api/types'

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
