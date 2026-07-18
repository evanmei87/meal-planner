import { Button, Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription } from 'meal-planner-web'

export function WithButton() {
  return (
    <Dialog>
      <DialogTrigger render={<Button>Open Dialog</Button>} />
      <DialogContent>
        <DialogTitle>Meal Details</DialogTitle>
        <DialogDescription>View and edit the selected meal.</DialogDescription>
      </DialogContent>
    </Dialog>
  )
}

export function OutlineVariant() {
  return (
    <Dialog>
      <DialogTrigger render={<Button variant="outline">View Plan</Button>} />
      <DialogContent>
        <DialogTitle>Weekly Plan</DialogTitle>
        <DialogDescription>Your meal plan for the week.</DialogDescription>
      </DialogContent>
    </Dialog>
  )
}
