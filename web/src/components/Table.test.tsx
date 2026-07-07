import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Table } from './Table'

describe('Table', () => {
  const columns = [
    { key: 'name', header: 'Name' },
    { key: 'qty', header: 'Qty' },
  ]

  it('renders headers and row cells', () => {
    render(<Table columns={columns} rows={[{ name: 'Apples', qty: 3 }]} />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Apples')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows an empty state when there are no rows', () => {
    render(<Table columns={columns} rows={[]} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('uses a custom cell renderer when provided', () => {
    const cols = [
      { key: 'name', header: 'Name', render: (v: unknown) => <b>{`!${String(v)}`}</b> },
    ]
    render(<Table columns={cols} rows={[{ name: 'X' }]} />)
    expect(screen.getByText('!X')).toBeInTheDocument()
  })

  it('calls onRowClick when a row is clicked', () => {
    const onRowClick = vi.fn()
    render(
      <Table
        columns={[{ key: 'name', header: 'Name' }]}
        rows={[{ name: 'Alpha' }]}
        onRowClick={onRowClick}
      />
    )
    fireEvent.click(screen.getByText('Alpha'))
    expect(onRowClick).toHaveBeenCalledWith({ name: 'Alpha' })
  })

  it('activates a row on Enter key', () => {
    const onRowClick = vi.fn()
    render(
      <Table
        columns={[{ key: 'name', header: 'Name' }]}
        rows={[{ name: 'Alpha' }]}
        onRowClick={onRowClick}
      />
    )
    fireEvent.keyDown(screen.getByText('Alpha').closest('tr')!, { key: 'Enter' })
    expect(onRowClick).toHaveBeenCalledWith({ name: 'Alpha' })
  })
})
