import { Dialog, DialogContent, DialogTitle, DialogDescription, Button } from 'meal-planner-web'

export function Short() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Remove Meal</DialogTitle>
        <DialogDescription>This will remove the meal from your plan.</DialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Remove</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function Long() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Update Weekly Meal Plan Preferences</DialogTitle>
        <DialogDescription>Changes apply to next week's generated plan.</DialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Discard</Button>
          <Button>Save Preferences</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
