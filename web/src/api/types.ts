export interface MealItem {
  name: string
  calories: number
  macros: { protein: number; carbs: number; fat: number }
  ingredients: string[]
}

export interface DayPlan {
  day: string
  meals: MealItem[]
  total_calories: number
  total_protein: number
  total_carbs: number
}

export interface GroceryListItem {
  item: string
  quantity: number
  unit: string
  category: string
}

export interface MealPlanRequest {
  days?: string[]
  preferences?: string
}

export interface MealPlanResponse {
  plan_id: string
  plan: DayPlan[]
  grocery_list: GroceryListItem[]
  status: string
  message?: string
}

export interface MealIngredient {
  name: string
  serving: string
  calories: number
  protein: number
  carbs: number
  fat: number
}

export interface MealResponse {
  name: string
  version: string
  category: string
  servings: number
  macros: { calories: number; protein: number; carbs: number; fat: number }
  ingredients: MealIngredient[]
  instructions: string[]
  tags: string[]
}

export interface AddMealRequest {
  name: string
  ingredients: MealIngredient[]
  macros: { calories: number; protein: number; carbs: number; fat: number }
  instructions: string[]
  category: string
  servings: number
  tags: string[]
}

export interface AddMealResponse {
  success: boolean
  meal_name: string
  newly_added: string[]
  category: string
  message: string
}

export interface SearchParams {
  category?: string
  min_cal?: number
  max_cal?: number
  min_prot?: number
  max_prot?: number
  min_carb?: number
  max_carb?: number
  min_fat?: number
  max_fat?: number
  ingredient?: string
  tag?: string
  search_term?: string
}

export interface GroceryParseResult {
  raw_phrase: string
  standardized_item: string
  quantity: number
  unit: string
  match: string
  confidence_score: number
  confidence_level: string
  status: 'auto' | 'review' | 'manual'
}

export interface GroceriesResponse {
  items: GroceryParseResult[]
  saved_count: number
  review_count: number
}

export type ExerciseType = 'running' | 'walking' | 'biking' | 'swimming' | 'strength'

export interface ExerciseItem {
  id: string
  type: ExerciseType
  distance_miles?: number | null
  duration_minutes: number
  sets?: number | null
  reps?: number | null
  calories: number
  notes?: string | null
  order: number
}

export interface ExerciseDayPlan {
  date: string
  day_name: string
  exercises: ExerciseItem[]
  total_calories: number
}

export interface ExerciseWeekResponse {
  week_start: string
  days: ExerciseDayPlan[]
}

export interface ExerciseMonthResponse {
  month: string
  days: ExerciseDayPlan[]
}

export interface AddExerciseRequest {
  date: string
  type: ExerciseType
  distance_miles?: number
  duration_minutes: number
  sets?: number
  reps?: number
  notes?: string
}

export interface UpdateExerciseRequest {
  type?: ExerciseType
  distance_miles?: number
  duration_minutes: number
  sets?: number
  reps?: number
  notes?: string
  date?: string
  order?: number
}

export interface ReorderExercisesRequest {
  date: string
  ordered_ids: string[]
}

export type PresetExercise = Omit<AddExerciseRequest, 'date'>

export interface AppState {
  current_day: string
  plan_id: string
  plan: DayPlan[]
  grocery_list: GroceryListItem[]
  missing_macros: string[]
  grocery_inventory: Record<string, unknown>[]
  unmatched_groceries: Record<string, unknown>[]
  inventory_usage: { used: string[]; unused: string[]; supplemental: string[] }
  preferences?: string
  normalized_exclusions?: string[]
}
