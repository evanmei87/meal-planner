interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-card text-card-foreground rounded-lg border border-border shadow-xs p-4 ${className}`}>
      {children}
    </div>
  )
}
