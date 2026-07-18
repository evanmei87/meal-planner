import { Button, Dialog, DialogContent, DialogTitle, DialogDescription } from 'meal-planner-web'

export function WithActions() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Generate Meal Plan</DialogTitle>
        <DialogDescription>
          Your plan will be generated based on your calorie goal and available ingredients.
        </DialogDescription>
        <p className="text-sm text-foreground mt-2">Estimated calories: 2,400 kcal/day</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Cancel</Button>
          <Button>Generate</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function WithForm() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Edit Servings</DialogTitle>
        <DialogDescription>Adjust the serving size for this meal.</DialogDescription>
        <div className="mt-3 flex items-center gap-3">
          <label className="text-sm font-medium text-foreground">Servings</label>
          <input
            type="number"
            defaultValue={2}
            className="w-20 rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-foreground"
          />
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Cancel</Button>
          <Button>Save</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
