'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import type { ChartJSON, ChartRendererProps } from './types'
import { BarChart } from './BarChart'
import { LineChart } from './LineChart'

/**
 * ChartRenderer - Wrapper component that parses chart JSON and renders the appropriate chart type
 *
 * Accepts either a JSON string or ChartJSON object and dynamically renders the correct chart.
 * Provides graceful error handling with fallback to error message display.
 *
 * Usage:
 * ```tsx
 * <ChartRenderer chartData='{"type":"bar","data":[...],"config":{...}}' />
 * <ChartRenderer chartData={chartJsonObject} />
 * ```
 */
const ChartRenderer: React.FC<ChartRendererProps> = ({
  chartData,
  className
}) => {
  const [error, setError] = React.useState<string | null>(null)
  const [parsedData, setParsedData] = React.useState<ChartJSON | null>(null)

  // Parse chart data on mount or when chartData changes
  React.useEffect(() => {
    try {
      let parsed: ChartJSON

      // Handle string input - parse as JSON
      if (typeof chartData === 'string') {
        parsed = JSON.parse(chartData) as ChartJSON
      } else {
        // Already an object
        parsed = chartData
      }

      // Validate parsed data structure
      if (!parsed.type || !parsed.data || !Array.isArray(parsed.data)) {
        throw new Error(
          'Invalid chart data: must include "type" and "data" array'
        )
      }

      // Validate chart type
      if (parsed.type !== 'bar' && parsed.type !== 'line') {
        throw new Error(
          `Invalid chart type "${parsed.type}": must be "bar" or "line"`
        )
      }

      // Validate config if provided
      if (parsed.config) {
        if (!parsed.config.xKey || !parsed.config.yKeys) {
          throw new Error(
            'Invalid chart config: must include "xKey" and "yKeys"'
          )
        }
      }

      setParsedData(parsed)
      setError(null)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to parse chart data'
      )
      setParsedData(null)
    }
  }, [chartData])

  // Render error state
  if (error) {
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
            <p className="mt-1 text-sm text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  // Render loading state
  if (!parsedData) {
    return (
      <div
        className={cn(
          'flex items-center justify-center rounded-lg border bg-muted/20 p-8',
          className
        )}
      >
        <div className="text-sm text-muted-foreground">Loading chart...</div>
      </div>
    )
  }

  // Extract config with defaults
  const config = parsedData.config || {}
  const {
    title,
    xKey = 'x',
    yKeys = ['y'],
    xAxisLabel,
    yAxisLabel,
    colors,
    height,
    width,
    showLegend,
    showGrid,
    stacked,
    showDots,
    curved
  } = config

  // Render appropriate chart based on type
  switch (parsedData.type) {
    case 'bar':
      return (
        <BarChart
          data={parsedData.data}
          xKey={xKey}
          yKeys={yKeys}
          title={title}
          xAxisLabel={xAxisLabel}
          yAxisLabel={yAxisLabel}
          colors={colors}
          height={height}
          width={width}
          className={className}
          showLegend={showLegend}
          showGrid={showGrid}
          stacked={stacked}
        />
      )

    case 'line':
      return (
        <LineChart
          data={parsedData.data}
          xKey={xKey}
          yKeys={yKeys}
          title={title}
          xAxisLabel={xAxisLabel}
          yAxisLabel={yAxisLabel}
          colors={colors}
          height={height}
          width={width}
          className={className}
          showLegend={showLegend}
          showGrid={showGrid}
          showDots={showDots}
          curved={curved}
        />
      )

    default:
      // This should never happen due to validation above
      return (
        <div
          className={cn(
            'rounded-lg border border-destructive bg-destructive/10 p-4',
            className
          )}
        >
          <p className="text-sm text-destructive">
            Unknown chart type: {parsedData.type}
          </p>
        </div>
      )
  }
}

ChartRenderer.displayName = 'ChartRenderer'

export { ChartRenderer }
export type { ChartRendererProps }
