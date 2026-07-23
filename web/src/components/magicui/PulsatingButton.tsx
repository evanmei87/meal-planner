import { motion, useReducedMotion } from 'framer-motion'
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
 * generation), inspired by MagicUI's "pulsating button" effect. Renders the
 * button unchanged, with no pulse, when the user prefers reduced motion.
 */
export function PulsatingButton({ pulsating = false, children, className }: PulsatingButtonProps) {
  const shouldReduceMotion = useReducedMotion()
  const showPulse = pulsating && !shouldReduceMotion

  return (
    <span className={cn('relative inline-flex', className)}>
      {showPulse && (
        <motion.span
          className="absolute inset-0 rounded bg-primary"
          animate={{ opacity: [0.35, 0], scale: [1, 1.4] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: 'easeOut' }}
          aria-hidden="true"
        />
      )}
      {children}
    </span>
  )
}
