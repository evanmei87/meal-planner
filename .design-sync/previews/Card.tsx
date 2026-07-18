import { Card } from 'meal-planner-web'

export function Basic() {
  return (
    <Card>
      <h3 className="font-semibold text-card-foreground">Grilled Chicken Bowl</h3>
      <p className="text-sm text-muted-foreground mt-1">Brown rice, roasted vegetables, and lemon tahini dressing.</p>
      <div className="mt-3 text-xs text-muted-foreground">680 cal · 52g protein · 64g carbs · 18g fat</div>
    </Card>
  )
}

export function WithCustomClass() {
  return (
    <Card className="max-w-xs">
      <h3 className="font-semibold text-card-foreground">Pre-Run Snack</h3>
      <p className="text-sm text-muted-foreground mt-1">Banana with almond butter.</p>
      <div className="mt-2 flex items-center gap-2">
        <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-md">Quick</span>
        <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-md">Pre-workout</span>
      </div>
    </Card>
  )
}

export function Stacked() {
  return (
    <div className="flex flex-col gap-3 max-w-sm">
      <Card>
        <div className="flex items-center justify-between">
          <span className="font-medium text-card-foreground">Monday Dinner</span>
          <span className="text-sm text-muted-foreground">720 cal</span>
        </div>
        <p className="text-sm text-muted-foreground mt-0.5">Salmon with asparagus and quinoa</p>
      </Card>
      <Card>
        <div className="flex items-center justify-between">
          <span className="font-medium text-card-foreground">Tuesday Dinner</span>
          <span className="text-sm text-muted-foreground">650 cal</span>
        </div>
        <p className="text-sm text-muted-foreground mt-0.5">Turkey stir-fry with brown rice</p>
      </Card>
    </div>
  )
}
