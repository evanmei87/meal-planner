import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { MealPlanRequest } from '@/api/types'

export function usePlan() {
  return useQuery({ queryKey: ['plan'], queryFn: api.plan.get })
}

export function useGeneratePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: MealPlanRequest) => api.plan.generate(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plan'] }),
  })
}
