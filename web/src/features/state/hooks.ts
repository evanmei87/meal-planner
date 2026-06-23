import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { AppState } from '../../api/types'

export function useAppState() {
  return useQuery({ queryKey: ['state'], queryFn: api.state.get })
}

export function useUpdateState() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (updates: Partial<AppState>) => api.state.update(updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['state'] }),
  })
}
