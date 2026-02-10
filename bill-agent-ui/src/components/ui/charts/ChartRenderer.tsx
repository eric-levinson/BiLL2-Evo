'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import type { ChartJSON, ChartRendererProps } from './types'
import { BarChart } from './BarChart'
import { LineChart } from './LineChart'

function parseChartData(
  chartData: string | ChartJSON
): { data: ChartJSON; error: null } | { data: null; error: string } {
  try {
    const parsed: ChartJSON =
      typeof chartData === 'string'
        ? (JSON.parse(chartData) as ChartJSON)
        : chartData

    if (!parsed.type || !parsed.data || !Array.isArray(parsed.data)) {
      return {
        data: null,
        error: 'Invalid chart data: must include "type" and "data" array'
      }
    }

    if (parsed.type !== 'bar' && parsed.type !== 'line') {
      return {
        data: null,
        error: `Invalid chart type "${parsed.type}": must be "bar" or "line"`
      }
    }

    if (parsed.config && (!parsed.config.xKey || !parsed.config.yKeys)) {
      return {
        data: null,
        error: 'Invalid chart config: must include "xKey" and "yKeys"'
      }
    }

    return { data: parsed, error: null }
  } catch (err) {
    return {
      data: null,
      error: err instanceof Error ? err.message : 'Failed to parse chart data'
    }
  }
}

const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  className
}) => {
  const result = React.useMemo(() => parseChartData(chartData), [chartData])

  if (!result.data) {
    return (
      <div
        className={cn(
          'rounded-lg border border-destructive bg-destructive/10 p-4',
          className
        )}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-destructive"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-medium text-destructive">
              Chart Error
            </h3>
            <p className="text-muted-foreground mt-1 text-sm">{result.error}</p>
          </div>
        </div>
      </div>
    )
  }

  const parsedData = result.data
  const config = parsedData.config
  const xKey = config?.xKey ?? 'x'
  const yKeys = config?.yKeys ?? ['y']

  const sharedProps = {
    data: parsedData.data,
    xKey,
    yKeys,
    title: config?.title,
    xAxisLabel: config?.xAxisLabel,
    yAxisLabel: config?.yAxisLabel,
    colors: config?.colors,
    height: config?.height,
    width: config?.width,
    className,
    showLegend: config?.showLegend,
    showGrid: config?.showGrid
  }

  switch (parsedData.type) {
    case 'bar':
      return <BarChart {...sharedProps} stacked={config?.stacked} />

    case 'line':
      return (
        <LineChart
          {...sharedProps}
          showDots={config?.showDots}
          curved={config?.curved}
        />
      )

    default:
      return (
        <div
          className={cn(
            'rounded-lg border border-destructive bg-destructive/10 p-4',
            className
          )}
        >
          <p className="text-sm text-destructive">
            Unknown chart type: {(parsedData as ChartJSON).type}
          </p>
        </div>
      )
  }
}

ChartRenderer.displayName = 'ChartRenderer'

export { ChartRenderer }
export type { ChartRendererProps }
