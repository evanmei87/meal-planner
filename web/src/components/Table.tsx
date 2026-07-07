export interface Column {
  key: string
  header: string
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode
}

interface TableProps {
  columns: Column[]
  rows: Record<string, unknown>[]
  onRowClick?: (row: Record<string, unknown>) => void
}

export function Table({ columns, rows, onRowClick }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border-collapse">
        <thead>
          <tr className="bg-muted">
            {columns.map((col, index) => (
              <th
                key={`${col.key}-${index}`}
                className="px-3 py-2 text-left font-semibold text-muted-foreground"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`border-t border-border hover:bg-muted/50 ${
                onRowClick ? 'cursor-pointer' : ''
              }`}
              {...(onRowClick
                ? {
                    role: 'button',
                    tabIndex: 0,
                    onClick: () => onRowClick(row),
                    onKeyDown: (e: React.KeyboardEvent) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onRowClick(row)
                      }
                    },
                  }
                : {})}
            >
              {columns.map((col, colIndex) => (
                <td key={`${col.key}-${colIndex}`} className="px-3 py-2 text-foreground">
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-4 text-center text-muted-foreground text-sm"
              >
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
