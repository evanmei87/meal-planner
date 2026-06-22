import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../../api/client'
import { Card } from '../../components/Card'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { usePlan, useGeneratePlan } from './hooks'

export function PlanPage() {
  const { data: planData, isLoading, isError, error } = usePlan()
  const generate = useGeneratePlan()
  const [selectedDay, setSelectedDay] = useState('')
  const [preferences, setPreferences] = useState('')

  const days = planData?.plan ?? []

  useEffect(() => {
    if (days.length > 0 && !selectedDay) {
      setSelectedDay(days[0].day)
    }
  }, [days, selectedDay])

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load plan'}
      />
    )

  const currentDayPlan = days.find((d) => d.day === selectedDay) ?? days[0]

  return (
    <div>
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          placeholder="Preferences (optional)"
          value={preferences}
          onChange={(e) => setPreferences(e.target.value)}
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={() => generate.mutate({ preferences: preferences || undefined })}
          disabled={generate.isPending}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
        >
          {generate.isPending ? 'Generating…' : 'Generate Plan'}
        </button>
      </div>

      {generate.isError && <ErrorBanner message="Failed to generate plan" />}

      {days.length === 0 ? (
        <p className="text-gray-500 text-sm">No plan yet — click Generate Plan.</p>
      ) : (
        <>
          <div className="flex gap-2 mb-4 flex-wrap">
            {days.map((d) => (
              <button
                key={d.day}
                onClick={() => setSelectedDay(d.day)}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  selectedDay === d.day
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {d.day}
              </button>
            ))}
          </div>

          {currentDayPlan && (
            <div>
              <p className="text-sm text-gray-500 mb-3">
                {currentDayPlan.total_calories} cal total · {currentDayPlan.total_protein}g protein ·{' '}
                {currentDayPlan.total_carbs}g carbs
              </p>
              <div className="grid gap-3">
                {currentDayPlan.meals.map((meal) => (
                  <Card key={meal.name}>
                    <Link
                      to={`/meals/${encodeURIComponent(meal.name)}`}
                      state={{ planMeal: meal }}
                      className="font-semibold hover:text-green-600"
                    >
                      {meal.name}
                    </Link>
                    <p className="text-sm text-gray-500 mt-1">
                      {meal.calories} kcal · {meal.macros.protein}g protein ·{' '}
                      {meal.macros.carbs}g carbs · {meal.macros.fat}g fat
                    </p>
                    {meal.ingredients.length > 0 && (
                      <p className="text-sm text-gray-600 mt-2">
                        {meal.ingredients.join(', ')}
                      </p>
                    )}
                  </Card>
                ))}
              </div>

              {(planData?.grocery_list.length ?? 0) > 0 && (
                <p className="mt-4 text-sm">
                  <Link to="/groceries" className="text-green-600 hover:underline">
                    View grocery list ({planData!.grocery_list.length} items) →
                  </Link>
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
