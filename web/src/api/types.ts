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

export interface MealResponse {
  name: string
  version: string
  category: string
  macros: { calories: number; protein: number; carbs: number; fat: number }
  ingredients: string[]
  instructions: string[]
  tags: string[]
}

export interface AddMealRequest {
  name: string
  ingredients: string[]
  macros: { calories: number; protein: number; carbs: number; fat: number }
  instructions: string[]
  category: string
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
