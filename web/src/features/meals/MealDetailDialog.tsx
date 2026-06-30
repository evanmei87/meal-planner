import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import type { MealResponse } from '@/api/types'
import { MealDetail } from '@/features/meals/MealDetail'

interface MealDetailDialogProps {
  meal: MealResponse | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function MealDetailDialog({ meal, open, onOpenChange }: MealDetailDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        {meal && (
          <>
            <DialogTitle className="sr-only">{meal.name}</DialogTitle>
            <MealDetail meal={meal} />
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
