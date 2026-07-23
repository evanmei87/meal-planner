import { useState } from 'react'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import { Table } from '@/components/Table'
import { Button } from '@/components/ui/button'
import type { AddMealRequest, MealIngredient, MealResponse, SearchParams } from '@/api/types'
import { ApiError } from '@/api/client'
import { useSearchMeals, useAddMeal } from '@/features/meals/hooks'
import { MealDetailDialog } from '@/features/meals/MealDetailDialog'

// Mirrors ExerciseCalendarPage's `inputClassName`: a bare `border` (no
// palette/border-color literal) so new inputs don't add to the ad-hoc-input
// count until a shared Input primitive exists (see .design-sync/north-star.md).
const ingredientInputClassName = 'w-full border rounded px-2 py-1 text-sm'

interface IngredientFormRow {
  name: string
  serving: string
  calories: string
  protein: string
  carbs: string
  fat: string
}

function emptyIngredientRow(): IngredientFormRow {
  return { name: '', serving: '', calories: '', protein: '', carbs: '', fat: '' }
}

function toMealIngredients(rows: IngredientFormRow[]): MealIngredient[] {
  return rows
    .filter((row) => row.name.trim())
    .map((row) => ({
      name: row.name.trim(),
      serving: row.serving.trim(),
      calories: parseInt(row.calories) || 0,
      protein: parseInt(row.protein) || 0,
      carbs: parseInt(row.carbs) || 0,
      fat: parseInt(row.fat) || 0,
    }))
}

export function MealsPage() {
  const [filters, setFilters] = useState<SearchParams>({})
  const [searchInput, setSearchInput] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [selectedMeal, setSelectedMeal] = useState<MealResponse | null>(null)
  const { data: meals, isLoading, isError, error } = useSearchMeals(filters)
  const addMeal = useAddMeal()

  const [form, setForm] = useState({
    name: '', calories: '', protein: '', carbs: '', fat: '',
    instructions: '', category: 'Dinner', servings: '1', tags: '',
  })
  const [ingredientRows, setIngredientRows] = useState<IngredientFormRow[]>([emptyIngredientRow()])

  const handleSearch = () => {
    setFilters(searchInput.trim() ? { search_term: searchInput.trim() } : {})
  }

  const updateIngredientRow = (index: number, field: keyof IngredientFormRow, value: string) => {
    setIngredientRows((rows) => rows.map((row, i) => (i === index ? { ...row, [field]: value } : row)))
  }

  const addIngredientRow = () => setIngredientRows((rows) => [...rows, emptyIngredientRow()])

  const removeIngredientRow = (index: number) => {
    setIngredientRows((rows) => rows.filter((_, i) => i !== index))
  }

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const req: AddMealRequest = {
      name: form.name,
      ingredients: toMealIngredients(ingredientRows),
      macros: {
        calories: parseInt(form.calories) || 0,
        protein: parseInt(form.protein) || 0,
        carbs: parseInt(form.carbs) || 0,
        fat: parseInt(form.fat) || 0,
      },
      instructions: form.instructions.split(';').map((s) => s.trim()).filter(Boolean),
      category: form.category,
      servings: parseInt(form.servings) || 1,
      tags: form.tags.split(',').map((s) => s.trim()).filter(Boolean),
    }
    addMeal.mutate(req, {
      onSuccess: () => {
        setShowAdd(false)
        setForm({ name: '', calories: '', protein: '', carbs: '', fat: '', instructions: '', category: 'Dinner', servings: '1', tags: '' })
        setIngredientRows([emptyIngredientRow()])
      },
    })
  }

  if (isLoading) return <Spinner />
  if (isError)
    return <ErrorBanner message={error instanceof ApiError ? error.message : 'Failed to load meals'} />

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Search meals…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm font-medium"
        >
          Search
        </button>
        <button
          onClick={() => setShowAdd((v) => !v)}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
        >
          Add Meal
        </button>
      </div>

      {showAdd && (
        <form onSubmit={handleAddSubmit} className="mb-6 bg-white border border-gray-200 rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-gray-800">New Meal</h2>
          <div>
            <label htmlFor="meal-name" className="block text-sm text-gray-600 mb-1">Meal name</label>
            <input id="meal-name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="block text-sm text-gray-600">Ingredients</span>
              <Button type="button" variant="outline" size="sm" onClick={addIngredientRow}>
                Add ingredient
              </Button>
            </div>
            <div className="space-y-2">
              {ingredientRows.map((row, index) => (
                <div key={index} className="grid grid-cols-8 gap-2 items-end">
                  <div className="col-span-2">
                    <label htmlFor={`ingredient-name-${index}`} className="block text-xs text-muted-foreground mb-1">
                      Ingredient {index + 1} name
                    </label>
                    <input
                      id={`ingredient-name-${index}`}
                      value={row.name}
                      onChange={(e) => updateIngredientRow(index, 'name', e.target.value)}
                      className={ingredientInputClassName}
                    />
                  </div>
                  <div>
                    <label htmlFor={`ingredient-serving-${index}`} className="block text-xs text-muted-foreground mb-1">
                      Ingredient {index + 1} serving
                    </label>
                    <input
                      id={`ingredient-serving-${index}`}
                      value={row.serving}
                      onChange={(e) => updateIngredientRow(index, 'serving', e.target.value)}
                      className={ingredientInputClassName}
                      placeholder="1 cup"
                    />
                  </div>
                  {(['calories', 'protein', 'carbs', 'fat'] as const).map((macro) => (
                    <div key={macro}>
                      <label htmlFor={`ingredient-${macro}-${index}`} className="block text-xs text-muted-foreground mb-1 capitalize">
                        Ingredient {index + 1} {macro}
                      </label>
                      <input
                        id={`ingredient-${macro}-${index}`}
                        type="number"
                        min="0"
                        value={row[macro]}
                        onChange={(e) => updateIngredientRow(index, macro, e.target.value)}
                        className={ingredientInputClassName}
                      />
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    disabled={ingredientRows.length === 1}
                    onClick={() => removeIngredientRow(index)}
                  >
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-4 gap-2">
            {(['calories', 'protein', 'carbs', 'fat'] as const).map((macro) => (
              <div key={macro}>
                <label className="block text-xs text-gray-500 mb-1 capitalize">{macro}</label>
                <input type="number" min="0" value={form[macro]} onChange={(e) => setForm({ ...form, [macro]: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
              </div>
            ))}
          </div>
          <div>
            <label htmlFor="meal-instructions" className="block text-sm text-gray-600 mb-1">Instructions (semicolon-separated)</label>
            <textarea id="meal-instructions" value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} rows={2} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                {['Breakfast', 'Lunch', 'Dinner', 'Snack'].map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="meal-servings" className="block text-sm text-gray-600 mb-1">Servings</label>
              <input id="meal-servings" type="number" min="1" value={form.servings} onChange={(e) => setForm({ ...form, servings: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Tags (comma-separated)</label>
              <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={addMeal.isPending} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm disabled:opacity-50">
              {addMeal.isPending ? 'Saving…' : 'Save Meal'}
            </button>
            <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm">
              Cancel
            </button>
          </div>
          {addMeal.isError && <ErrorBanner message="Failed to add meal" />}
        </form>
      )}

      <Table
        columns={[
          { key: 'name', header: 'Name' },
          { key: 'category', header: 'Category' },
          { key: 'macros', header: 'Calories', render: (v) => (v as { calories: number }).calories },
          { key: 'macros', header: 'Protein', render: (v) => `${(v as { protein: number }).protein}g` },
          { key: 'macros', header: 'Carbs', render: (v) => `${(v as { carbs: number }).carbs}g` },
          { key: 'macros', header: 'Fat', render: (v) => `${(v as { fat: number }).fat}g` },
        ]}
        rows={(meals ?? []) as unknown as Record<string, unknown>[]}
        onRowClick={(row) => setSelectedMeal(row as unknown as MealResponse)}
      />
      <MealDetailDialog
        meal={selectedMeal}
        open={selectedMeal !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedMeal(null)
        }}
      />
    </div>
  )
}
