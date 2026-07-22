export function getTodayInEST(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })
}

export function getCurrentWeekDates(
  referenceISODate: string = getTodayInEST()
): { date: string; dayName: string }[] {
  const reference = new Date(`${referenceISODate}T00:00:00`)
  const daysSinceMonday = (reference.getDay() + 6) % 7
  const monday = new Date(reference)
  monday.setDate(reference.getDate() - daysSinceMonday)

  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(monday)
    day.setDate(monday.getDate() + i)
    return {
      date: day.toLocaleDateString('en-CA'),
      dayName: day.toLocaleDateString('en-US', { weekday: 'long' }),
    }
  })
}
