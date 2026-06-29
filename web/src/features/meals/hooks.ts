import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { AddMealRequest, SearchParams } from '@/api/types'

export function useMeals() {
  return useQuery({ queryKey: ['meals'], queryFn: () => api.meals.list() })
}

export function useSearchMeals(params: SearchParams) {
  return useQuery({
    queryKey: ['meals', 'search', params],
    queryFn: () => api.meals.search(params),
  })
}

export function useAddMeal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: AddMealRequest) => api.meals.add(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['meals'] }),
  })
}
