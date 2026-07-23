import { Card } from '@/components/Card'
import { Table } from '@/components/Table'
import type { MealResponse } from '@/api/types'
import { StatTile, MacroBar } from '@/features/meals/MacroDisplay'

export function MealDetail({ meal }: { meal: MealResponse }) {
  const servingLabel = `Makes ${meal.servings} serving${meal.servings === 1 ? '' : 's'}`

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{meal.name}</h1>
      <p className="text-sm text-muted-foreground mb-1">{meal.category}</p>
      <p className="text-sm text-muted-foreground mb-4">{servingLabel}</p>

      <div className="mb-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
          Per serving
        </p>
        <div className="grid grid-cols-4 gap-2 mb-3">
          <StatTile label="Calories" value={String(meal.macros.calories)} />
          <StatTile label="Protein" value={`${meal.macros.protein}g`} />
          <StatTile label="Carbs" value={`${meal.macros.carbs}g`} />
          <StatTile label="Fat" value={`${meal.macros.fat}g`} />
        </div>
        <MacroBar
          protein={meal.macros.protein}
          carbs={meal.macros.carbs}
          fat={meal.macros.fat}
        />
      </div>

      <Card className="mb-4">
        <h2 className="font-semibold mb-2">Ingredients</h2>
        <Table
          columns={[
            { key: 'name', header: 'Ingredient' },
            { key: 'serving', header: 'Serving' },
            { key: 'calories', header: 'Calories' },
            { key: 'protein', header: 'Protein', render: (v) => `${v}g` },
            { key: 'carbs', header: 'Carbs', render: (v) => `${v}g` },
            { key: 'fat', header: 'Fat', render: (v) => `${v}g` },
          ]}
          rows={meal.ingredients as unknown as Record<string, unknown>[]}
        />
      </Card>

      <Card>
        <h2 className="font-semibold mb-2">Instructions</h2>
        <ol className="list-decimal pl-5 text-sm text-foreground space-y-1">
          {meal.instructions.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>
      </Card>

      {meal.tags.length > 0 && (
        <div className="mt-4 flex gap-2 flex-wrap">
          {meal.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-muted text-muted-foreground text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
