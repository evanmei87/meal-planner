import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface BlurFadeProps {
  /** Changing this key remounts the wrapper, re-triggering the reveal (e.g. a selected day/tab id). */
  transitionKey: string
  children: ReactNode
  className?: string
}

/**
 * Subtle fade + slide-up reveal for content that swaps on tab/day selection
 * (MagicUI's "blur fade" pattern). Remounting on `transitionKey` change
 * replays `tw-animate-css`'s enter animation; `motion-reduce:animate-none`
 * renders already-settled when the user prefers reduced motion.
 */
export function BlurFade({ transitionKey, children, className }: BlurFadeProps) {
  return (
    <div
      key={transitionKey}
      className={cn('animate-in fade-in slide-in-from-bottom-2 duration-200 motion-reduce:animate-none', className)}
    >
      {children}
    </div>
  )
}
