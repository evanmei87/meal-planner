import { Dialog, DialogContent, DialogTitle, DialogDescription, Button } from 'meal-planner-web'

export function Informational() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Grocery List Ready</DialogTitle>
        <DialogDescription>
          23 items have been added to your list based on this week's meal plan.
          Items you already have in inventory are not included.
        </DialogDescription>
        <div className="mt-4 flex justify-end">
          <Button>View List</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function Warning() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Replace Current Plan?</DialogTitle>
        <DialogDescription>
          Generating a new plan will replace your existing one.
          Any custom meals you've added will be lost.
        </DialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="outline">Keep Current</Button>
          <Button>Generate New</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
