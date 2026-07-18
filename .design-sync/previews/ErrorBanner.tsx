import { ErrorBanner } from 'meal-planner-web'

export function ApiError() {
  return <ErrorBanner message="Failed to load meal plan. Please try again." />
}

export function ValidationError() {
  return <ErrorBanner message="Servings must be a number between 1 and 10." />
}

export function NetworkError() {
  return <ErrorBanner message="No internet connection. Check your network and retry." />
}
