import { useState } from 'react'
import { ApiError } from '@/api/client'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import { Table } from '@/components/Table'
import { useAppState } from '@/features/state/hooks'
import type { GroceryParseResult } from '@/api/types'
import { useAddGroceries } from '@/features/groceries/hooks'

export function GroceriesPage() {
  const [text, setText] = useState('')
  const { data: state, isLoading, isError, error } = useAppState()
  const addGroceries = useAddGroceries()

  const handleAdd = () => {
    if (!text.trim()) return
    addGroceries.mutate(text, { onSuccess: () => setText('') })
  }

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load state'}
      />
    )

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-lg font-semibold mb-3">Add Groceries</h2>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="I got two pounds of chicken thighs, spinach…"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={handleAdd}
            disabled={addGroceries.isPending || !text.trim()}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
          >
            {addGroceries.isPending ? 'Parsing…' : 'Add'}
          </button>
        </div>
        {addGroceries.isError && <ErrorBanner message="Failed to parse groceries" />}
        {addGroceries.data && (
          <ParseResultTable
            result={addGroceries.data.items}
            savedCount={addGroceries.data.saved_count}
            reviewCount={addGroceries.data.review_count}
          />
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Grocery List</h2>
        {(state?.grocery_list.length ?? 0) === 0 ? (
          <p className="text-sm text-gray-400">No grocery list yet.</p>
        ) : (
          <Table
            columns={[
              { key: 'item', header: 'Item' },
              { key: 'quantity', header: 'Qty' },
              { key: 'unit', header: 'Unit' },
              { key: 'category', header: 'Category' },
            ]}
            rows={state!.grocery_list as unknown as Record<string, unknown>[]}
          />
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Inventory</h2>
        {(state?.grocery_inventory.length ?? 0) === 0 ? (
          <p className="text-sm text-gray-400">No inventory yet.</p>
        ) : (
          <Table
            columns={[
              { key: 'standardized_item', header: 'Item' },
              { key: 'quantity', header: 'Qty' },
              { key: 'unit', header: 'Unit' },
            ]}
            rows={state!.grocery_inventory}
          />
        )}
      </section>
    </div>
  )
}

function ParseResultTable({
  result,
  savedCount,
  reviewCount,
}: {
  result: GroceryParseResult[]
  savedCount: number
  reviewCount: number
}) {
  return (
    <div>
      <p className="text-sm text-gray-600 mb-2">
        Saved: {savedCount} · Review/Manual: {reviewCount}
      </p>
      <Table
        columns={[
          { key: 'raw_phrase', header: 'Raw' },
          { key: 'standardized_item', header: 'Standardized' },
          { key: 'quantity', header: 'Qty' },
          { key: 'unit', header: 'Unit' },
          { key: 'match', header: 'Match' },
          {
            key: 'confidence_score',
            header: 'Confidence',
            render: (v) => Number(v).toFixed(2),
          },
          { key: 'status', header: 'Status' },
        ]}
        rows={result as unknown as Record<string, unknown>[]}
      />
    </div>
  )
}
