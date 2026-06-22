import { NavLink, Outlet } from 'react-router-dom'

export function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex gap-6 text-sm font-medium">
          <NavLink
            to="/plan"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            Plan
          </NavLink>
          <NavLink
            to="/meals"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            Meals
          </NavLink>
          <NavLink
            to="/groceries"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            Groceries
          </NavLink>
          <NavLink
            to="/state"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            State
          </NavLink>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
