import { useMemo, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table'
import { formatValue, isNumeric } from '../../lib/formatters'

interface DataTableProps {
  columns: string[]
  rows: Record<string, unknown>[]
}

function exportCsv(columns: string[], rows: Record<string, unknown>[]) {
  const header = columns.join(',')
  const body = rows
    .map(row => columns.map(col => {
      const v = row[col]
      const str = String(v ?? '')
      return str.includes(',') || str.includes('"') || str.includes('\n')
        ? `"${str.replace(/"/g, '""')}"`
        : str
    }).join(','))
    .join('\n')
  const blob = new Blob([`${header}\n${body}`], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'query-results.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function DataTable({ columns, rows }: DataTableProps) {
  const [copied, setCopied] = useState(false)

  const columnDefs = useMemo<ColumnDef<Record<string, unknown>>[]>(
    () =>
      columns.map(col => {
        const isNumericCol = rows.some(r => isNumeric(r[col]))
        return {
          id: col,
          accessorFn: (row: Record<string, unknown>) => row[col],
          header: col.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          cell: ({ getValue }) => {
            const val = getValue<unknown>()
            return (
              <span className={isNumeric(val) ? 'font-mono tabular-nums' : ''}>
                {formatValue(val)}
              </span>
            )
          },
          meta: { numeric: isNumericCol },
        }
      }),
    [columns, rows]
  )

  const table = useReactTable({
    data: rows,
    columns: columnDefs,
    getCoreRowModel: getCoreRowModel(),
  })

  const handleCopy = async () => {
    const header = columns.join('\t')
    const body = rows
      .map(row => columns.map(col => String(row[col] ?? '')).join('\t'))
      .join('\n')
    await navigator.clipboard.writeText(`${header}\n${body}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-end gap-2">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono
                     bg-surface2 border border-border text-muted hover:text-text
                     hover:border-accent/40 transition-all"
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          {copied ? 'Copied!' : 'Copy'}
        </button>
        <button
          onClick={() => exportCsv(columns, rows)}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono
                     bg-surface2 border border-border text-muted hover:text-text
                     hover:border-accent/40 transition-all"
        >
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          CSV
        </button>
      </div>

      <div className="max-h-[360px] overflow-auto rounded-lg border border-border">
        <table className="w-full text-sm border-collapse">
          <thead className="sticky top-0 bg-surface2 z-10">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(header => {
                  const numeric = (header.column.columnDef.meta as { numeric?: boolean } | undefined)?.numeric
                  return (
                    <th
                      key={header.id}
                      className={`px-3 py-2.5 text-xs font-medium text-muted uppercase tracking-wider border-b border-border whitespace-nowrap ${
                        numeric ? 'text-right' : 'text-left'
                      }`}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, i) => (
              <tr
                key={row.id}
                className={i % 2 === 0 ? 'bg-surface' : 'bg-surface2'}
              >
                {row.getVisibleCells().map(cell => {
                  const numeric = (cell.column.columnDef.meta as { numeric?: boolean } | undefined)?.numeric
                  return (
                    <td
                      key={cell.id}
                      className={`px-3 py-2 text-dim border-b border-border/40 ${
                        numeric ? 'text-right' : 'text-left'
                      }`}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
