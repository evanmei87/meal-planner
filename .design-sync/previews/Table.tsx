import { Table } from 'meal-planner-web'
import type { Column } from 'meal-planner-web'

const mealColumns: Column[] = [
  { key: 'day', header: 'Day' },
  { key: 'meal', header: 'Meal' },
  { key: 'calories', header: 'Calories' },
  { key: 'protein', header: 'Protein' },
]

const mealRows = [
  { day: 'Monday', meal: 'Grilled Chicken Bowl', calories: '680', protein: '52g' },
  { day: 'Tuesday', meal: 'Salmon & Quinoa', calories: '720', protein: '48g' },
  { day: 'Wednesday', meal: 'Turkey Stir-fry', calories: '650', protein: '44g' },
  { day: 'Thursday', meal: 'Lentil Soup', calories: '520', protein: '28g' },
]

export function MealPlan() {
  return (
    <div className="w-full max-w-xl">
      <Table columns={mealColumns} rows={mealRows} />
    </div>
  )
}

export function Clickable() {
  return (
    <div className="w-full max-w-xl">
      <Table
        columns={mealColumns}
        rows={mealRows}
        onRowClick={(row) => {}}
      />
    </div>
  )
}

export function Empty() {
  return (
    <div className="w-full max-w-xl">
      <Table columns={mealColumns} rows={[]} />
    </div>
  )
}
