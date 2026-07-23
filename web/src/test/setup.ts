import '@testing-library/jest-dom'

// jsdom has no ResizeObserver; Recharts' ResponsiveContainer (used by Tremor charts) requires one.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverStub
