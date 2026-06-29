import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import { Table } from '@/components/Table'
import { useGeneratePlan } from '@/features/plan/hooks'
import { useAppState, useUpdateState } from '@/features/state/hooks'

export function StatePage() {
  const { data: state, isLoading, isError, error } = useAppState()
  const updateState = useUpdateState()
  const generatePlan = useGeneratePlan()
  const qc = useQueryClient()
  const [preferencesInput, setPreferencesInput] = useState('')
  const prefInitialized = useRef(false)

  useEffect(() => {
    if (state !== undefined && !prefInitialized.current) {
      setPreferencesInput(state.preferences ?? '')
      prefInitialized.current = true
    }
  }, [state])

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load state'}
      />
    )
  if (!state) return null

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-lg font-semibold mb-3">Preferences</h2>
        <div className="flex gap-3 max-w-lg">
          <input
            type="text"
            value={preferencesInput}
            onChange={(e) => setPreferencesInput(e.target.value)}
            placeholder="e.g. no red meat, high protein, vegetarian lunches"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={() => updateState.mutate({ preferences: preferencesInput })}
            disabled={updateState.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
          >
            {updateState.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
        {state.plan_id && (
          <button
            onClick={() =>
              generatePlan.mutate(
                { preferences: preferencesInput || undefined },
                {
                  onSuccess: () => {
                    qc.invalidateQueries({ queryKey: ['state'] })
                    qc.invalidateQueries({ queryKey: ['plan'], refetchType: 'all' })
                  },
                }
              )
            }
            disabled={generatePlan.isPending}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
          >
            {generatePlan.isPending ? 'Regenerating…' : 'Regenerate Plan'}
          </button>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Current State</h2>
        <dl className="grid grid-cols-2 gap-y-2 gap-x-4 text-sm max-w-sm">
          <dt className="text-gray-500">Current Day</dt>
          <dd className="font-medium">{state.current_day}</dd>
          <dt className="text-gray-500">Plan ID</dt>
          <dd className="font-mono text-xs truncate">{state.plan_id}</dd>
        </dl>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Inventory Usage</h2>
        <div className="grid grid-cols-3 gap-4 text-sm">
          {(
            [
              { label: 'Used', key: 'used' as const, color: 'text-green-600' },
              { label: 'Unused', key: 'unused' as const, color: 'text-gray-500' },
              { label: 'Supplemental', key: 'supplemental' as const, color: 'text-blue-600' },
            ] as const
          ).map(({ label, key, color }) => (
            <div key={key}>
              <h3 className={`font-medium mb-1 ${color}`}>
                {label} ({state.inventory_usage[key].length})
              </h3>
              <ul className="space-y-0.5 text-gray-700">
                {state.inventory_usage[key].map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {state.inventory_usage[key].length === 0 && (
                  <li className="text-gray-400">—</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {state.unmatched_groceries.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Unmatched Groceries</h2>
          <Table
            columns={[
              { key: 'raw_phrase', header: 'Raw' },
              { key: 'standardized_item', header: 'Standardized' },
              { key: 'source', header: 'Source' },
            ]}
            rows={state.unmatched_groceries}
          />
        </section>
      )}

      {state.missing_macros.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Missing Macros</h2>
          <ul className="text-sm text-gray-700 list-disc pl-5 space-y-1">
            {state.missing_macros.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
