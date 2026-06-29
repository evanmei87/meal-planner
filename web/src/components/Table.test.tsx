import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
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
})
