interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg shadow-xs border border-gray-200 p-4 ${className}`}>
      {children}
    </div>
  )
}
