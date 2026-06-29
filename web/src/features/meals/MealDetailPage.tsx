import { useLocation, useParams } from 'react-router-dom'
import { ApiError } from '@/api/client'
import { Card } from '@/components/Card'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import type { MealItem } from '@/api/types'
import { useMeals } from '@/features/meals/hooks'

export function MealDetailPage() {
  const { name } = useParams<{ name: string }>()
  const location = useLocation()
  const decodedName = decodeURIComponent(name ?? '')
  const { data: meals, isLoading, isError, error } = useMeals()

  const planMeal = (location.state as { planMeal?: MealItem } | null)?.planMeal
  const savedMeal = meals?.find((m) => m.name === decodedName)

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load meals'}
      />
    )

  if (savedMeal) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-1">{savedMeal.name}</h1>
        <p className="text-sm text-gray-500 mb-1">{savedMeal.category}</p>
        <p className="text-sm text-gray-600 mb-4">
          {savedMeal.macros.calories} kcal · {savedMeal.macros.protein}g protein ·{' '}
          {savedMeal.macros.carbs}g carbs · {savedMeal.macros.fat}g fat
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <h2 className="font-semibold mb-2">Ingredients</h2>
            <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
              {savedMeal.ingredients.map((ing) => <li key={ing}>{ing}</li>)}
            </ul>
          </Card>
          <Card>
            <h2 className="font-semibold mb-2">Instructions</h2>
            <ol className="list-decimal pl-5 text-sm text-gray-700 space-y-1">
              {savedMeal.instructions.map((step, i) => <li key={i}>{step}</li>)}
            </ol>
          </Card>
        </div>
        {savedMeal.tags.length > 0 && (
          <div className="mt-4 flex gap-2 flex-wrap">
            {savedMeal.tags.map((tag) => (
              <span key={tag} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (planMeal) {
    return (
      <div>
        <div className="mb-3 rounded bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
          This meal is not in your saved library.
        </div>
        <h1 className="text-2xl font-bold mb-2">{planMeal.name}</h1>
        <p className="text-sm text-gray-600 mb-4">
          {planMeal.calories} kcal · {planMeal.macros.protein}g protein ·{' '}
          {planMeal.macros.carbs}g carbs · {planMeal.macros.fat}g fat
        </p>
        {planMeal.ingredients.length > 0 && (
          <Card>
            <h2 className="font-semibold mb-2">Ingredients</h2>
            <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
              {planMeal.ingredients.map((ing) => <li key={ing}>{ing}</li>)}
            </ul>
          </Card>
        )}
      </div>
    )
  }

  return <p className="text-gray-500">Meal "{decodedName}" not found.</p>
}
