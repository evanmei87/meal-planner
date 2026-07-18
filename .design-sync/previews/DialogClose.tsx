import { Button, Dialog, DialogClose, DialogContent, DialogTitle, DialogDescription } from 'meal-planner-web'

export function InOpenDialog() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Preferences Saved</DialogTitle>
        <DialogDescription>Your dietary preferences have been updated.</DialogDescription>
        <div className="mt-4 flex justify-end">
          <DialogClose render={<Button>Done</Button>} />
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function OutlineClose() {
  return (
    <Dialog defaultOpen>
      <DialogContent>
        <DialogTitle>Add Ingredients</DialogTitle>
        <DialogDescription>Select items to add to your grocery list.</DialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <DialogClose render={<Button variant="outline">Cancel</Button>} />
          <Button>Add</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
