import { afterEach, describe, expect, it, vi } from 'vitest'
import { getTodayInEST, getCurrentWeekDates } from './dateUtils'

afterEach(() => {
  vi.useRealTimers()
})

describe('getTodayInEST', () => {
  it('returns the date in America/New_York as YYYY-MM-DD', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00'))
    expect(getTodayInEST()).toBe('2026-06-24')
  })

  it('resolves to the previous EST day when UTC has already rolled over', () => {
    // 2026-06-25T02:00:00Z is 2026-06-24T22:00:00 in New York (EDT, UTC-4) — still the 24th locally.
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-25T02:00:00Z'))
    expect(getTodayInEST()).toBe('2026-06-24')
  })
})

describe('getCurrentWeekDates', () => {
  it('returns Monday through Sunday for a Wednesday reference date', () => {
    const week = getCurrentWeekDates('2026-06-24') // a Wednesday
    expect(week).toEqual([
      { date: '2026-06-22', dayName: 'Monday' },
      { date: '2026-06-23', dayName: 'Tuesday' },
      { date: '2026-06-24', dayName: 'Wednesday' },
      { date: '2026-06-25', dayName: 'Thursday' },
      { date: '2026-06-26', dayName: 'Friday' },
      { date: '2026-06-27', dayName: 'Saturday' },
      { date: '2026-06-28', dayName: 'Sunday' },
    ])
  })

  it('returns the same week when the reference date is a Sunday', () => {
    const week = getCurrentWeekDates('2026-06-28') // a Sunday
    expect(week[0].date).toBe('2026-06-22')
    expect(week[6].date).toBe('2026-06-28')
  })

  it('defaults to the week containing today in EST when no reference date is given', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00'))
    const week = getCurrentWeekDates()
    expect(week[2].date).toBe('2026-06-24')
    expect(week[2].dayName).toBe('Wednesday')
  })
})
