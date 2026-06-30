import { useLocation, useParams } from 'react-router-dom'
import { ApiError } from '@/api/client'
import { Card } from '@/components/Card'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Spinner } from '@/components/Spinner'
import type { MealItem } from '@/api/types'
import { useMeals } from '@/features/meals/hooks'
import { MealDetail } from '@/features/meals/MealDetail'

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
    return <MealDetail meal={savedMeal} />
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
