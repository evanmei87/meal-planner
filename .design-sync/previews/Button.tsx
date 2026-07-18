import { Button } from 'meal-planner-web'

export function Variants() {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <Button variant="default">Generate Plan</Button>
      <Button variant="outline">Edit</Button>
      <Button variant="secondary">Save Draft</Button>
      <Button variant="ghost">Cancel</Button>
      <Button variant="destructive">Delete</Button>
      <Button variant="link">View details</Button>
    </div>
  )
}

export function Sizes() {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <Button size="xs">XSmall</Button>
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
    </div>
  )
}

export function States() {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <Button>Active</Button>
      <Button disabled>Disabled</Button>
    </div>
  )
}

export function IconSizes() {
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <Button size="icon" variant="outline" aria-label="Add">+</Button>
      <Button size="icon-sm" variant="ghost" aria-label="Remove">×</Button>
      <Button size="icon-lg" variant="default" aria-label="Menu">≡</Button>
    </div>
  )
}
