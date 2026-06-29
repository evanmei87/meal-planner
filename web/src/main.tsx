import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { App } from '@/App'
import { PlanPage } from '@/features/plan/PlanPage'
import { MealsPage } from '@/features/meals/MealsPage'
import { MealDetailPage } from '@/features/meals/MealDetailPage'
import { GroceriesPage } from '@/features/groceries/GroceriesPage'
import { StatePage } from '@/features/state/StatePage'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />}>
            <Route index element={<Navigate to="/plan" replace />} />
            <Route path="plan" element={<PlanPage />} />
            <Route path="meals" element={<MealsPage />} />
            <Route path="meals/:name" element={<MealDetailPage />} />
            <Route path="groceries" element={<GroceriesPage />} />
            <Route path="state" element={<StatePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
