import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

export function useAppState() {
  return useQuery({ queryKey: ['state'], queryFn: api.state.get })
}
