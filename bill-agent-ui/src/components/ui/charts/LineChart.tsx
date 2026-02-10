'use client'

import * as React from 'react'
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

import { cn } from '@/lib/utils'
import type { LineChartProps } from './types'

// Default color palette for chart lines (fantasy football themed)
const DEFAULT_COLORS = [
  '#3b82f6', // blue-500
  '#10b981', // green-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#06b6d4', // cyan-500
  '#f97316' // orange-500
]

const LineChart = React.forwardRef<HTMLDivElement, LineChartProps>(
  (
    {
      data,
      xKey,
      yKeys,
      title,
      xAxisLabel,
      yAxisLabel,
      colors = DEFAULT_COLORS,
      height = 400,
      width = '100%',
      className,
      showLegend = true,
      showGrid = true,
      showDots = true,
      curved = true
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'bg-card text-card-foreground rounded-xl border shadow-sm',
          className
        )}
      >
        {title && (
          <div className="flex flex-col space-y-1.5 p-6 pb-4">
            <h3 className="font-semibold leading-none tracking-tight">
              {title}
            </h3>
          </div>
        )}
        <div className="p-6 pt-0">
          <ResponsiveContainer width={width} height={height}>
            <RechartsLineChart
              data={data}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: xAxisLabel ? 30 : 5
              }}
            >
              {showGrid && (
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              )}
              <XAxis
                dataKey={xKey}
                label={
                  xAxisLabel
                    ? {
                        value: xAxisLabel,
                        position: 'insideBottom',
                        offset: -20
                      }
                    : undefined
                }
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: 'currentColor', strokeOpacity: 0.3 }}
              />
              <YAxis
                label={
                  yAxisLabel
                    ? {
                        value: yAxisLabel,
                        angle: -90,
                        position: 'insideLeft'
                      }
                    : undefined
                }
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: 'currentColor', strokeOpacity: 0.3 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem'
                }}
                cursor={{ stroke: 'hsl(var(--muted))', strokeWidth: 2 }}
              />
              {showLegend && (
                <Legend
                  wrapperStyle={{ fontSize: '0.875rem', paddingTop: '1rem' }}
                />
              )}
              {yKeys.map((key, index) => (
                <Line
                  key={key}
                  type={curved ? 'monotone' : 'linear'}
                  dataKey={key}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={showDots}
                  activeDot={{ r: 6 }}
                />
              ))}
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }
)

LineChart.displayName = 'LineChart'

export { LineChart }
export type { LineChartProps }
