import { test } from 'node:test'
import assert from 'node:assert/strict'
import { evaluateGate } from './ds-check.mjs'

test('passes when counts equal the baseline', () => {
  const result = evaluateGate({ 'no-bare-button': 9 }, { 'no-bare-button': 9 })
  assert.equal(result.ok, true)
  assert.deepEqual(result.regressions, [])
  assert.deepEqual(result.improvements, [])
})

test('fails when a count exceeds the baseline', () => {
  const result = evaluateGate({ 'no-bare-button': 10 }, { 'no-bare-button': 9 })
  assert.equal(result.ok, false)
  assert.deepEqual(result.regressions, [{ id: 'no-bare-button', was: 9, now: 10 }])
})

test('passes and reports an improvement when a count drops', () => {
  const result = evaluateGate({ 'no-bare-button': 8 }, { 'no-bare-button': 9 })
  assert.equal(result.ok, true)
  assert.deepEqual(result.improvements, [{ id: 'no-bare-button', was: 9, now: 8 }])
})

test('treats a rule missing from the baseline as a zero ceiling', () => {
  const result = evaluateGate({ 'new-rule': 1 }, {})
  assert.equal(result.ok, false, 'an unbaselined rule must not pass silently')
  assert.deepEqual(result.regressions, [{ id: 'new-rule', was: 0, now: 1 }])
})

test('reports every regression, not just the first', () => {
  const result = evaluateGate(
    { 'no-bare-button': 10, 'no-raw-palette': 70 },
    { 'no-bare-button': 9, 'no-raw-palette': 69 },
  )
  assert.equal(result.regressions.length, 2)
})
