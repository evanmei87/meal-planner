import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PulsatingButtonProps {
  /** True while the action the button triggers is in progress. */
  pulsating?: boolean
  children: ReactNode
  className?: string
}

/**
 * Wraps a button with a soft pulsing ring behind it while `pulsating` is
 * true — in-progress feedback for long-running actions (e.g. plan
 * generation), inspired by MagicUI's "pulsating button" effect. Uses
 * Tailwind's `animate-ping` keyframe loop; `motion-reduce:animate-none`
 * freezes the ring when the user prefers reduced motion.
 */
export function PulsatingButton({ pulsating = false, children, className }: PulsatingButtonProps) {
  return (
    <span className={cn('relative inline-flex', className)}>
      {pulsating && (
        <span
          className="absolute inset-0 rounded bg-primary animate-ping motion-reduce:animate-none"
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  )
}
