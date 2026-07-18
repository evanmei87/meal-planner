import { Button, Dialog, DialogContent, DialogTitle, DialogDescription } from 'meal-planner-web'

export function Open() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Add to Grocery List</DialogTitle>
        <DialogDescription>
          This will add all missing ingredients to your grocery list.
        </DialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Cancel</Button>
          <Button>Add Items</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function ConfirmDelete() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Remove Meal</DialogTitle>
        <DialogDescription>
          Are you sure you want to remove this meal from Tuesday's plan?
          This cannot be undone.
        </DialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Keep Meal</Button>
          <Button variant="destructive">Remove</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
