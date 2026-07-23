import '@testing-library/jest-dom'

// jsdom has no ResizeObserver; Recharts' ResponsiveContainer (used by Tremor charts) requires one.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverStub

// jsdom has no matchMedia; framer-motion's useReducedMotion() reads
// `(prefers-reduced-motion: reduce)` to decide whether to animate.
window.matchMedia ??= (query: string) =>
  ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as MediaQueryList
