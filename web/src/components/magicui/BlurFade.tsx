import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

interface BlurFadeProps {
  /** Changing this key remounts the wrapper, re-triggering the reveal (e.g. a selected day/tab id). */
  transitionKey: string
  children: ReactNode
  className?: string
}

/**
 * Subtle fade + slide-up reveal for content that swaps on tab/day selection
 * (MagicUI's "blur fade" pattern). Skips the animation and renders already
 * settled when the user prefers reduced motion.
 */
export function BlurFade({ transitionKey, children, className }: BlurFadeProps) {
  const shouldReduceMotion = useReducedMotion()

  return (
    <motion.div
      key={transitionKey}
      initial={shouldReduceMotion ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
