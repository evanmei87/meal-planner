import { Spinner } from 'meal-planner-web'

export function Default() {
  return <Spinner />
}

export function InContext() {
  return (
    <div className="flex flex-col items-center gap-2">
      <Spinner />
      <p className="text-sm text-muted-foreground">Generating your meal plan…</p>
    </div>
  )
}
