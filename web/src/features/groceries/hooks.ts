import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'

export function useAddGroceries() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => api.groceries.add(text),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['state'] }),
  })
}
