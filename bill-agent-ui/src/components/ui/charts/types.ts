import { type HTMLAttributes, type DetailedHTMLProps } from 'react'

// Base data point structure for all charts
interface ChartDataPoint {
  [key: string]: string | number | null | undefined
}

// Chart data structure
interface ChartData {
  labels?: string[]
  datasets?: ChartDataset[]
  data?: ChartDataPoint[]
}

// Dataset for multi-series charts
interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string | string[]
  borderWidth?: number
  fill?: boolean
}

// Chart axis configuration
interface ChartAxis {
  label?: string
  min?: number
  max?: number
  ticks?: {
    stepSize?: number
    callback?: (value: number) => string
  }
}

// Chart legend configuration
interface ChartLegend {
  display?: boolean
  position?: 'top' | 'bottom' | 'left' | 'right'
  align?: 'start' | 'center' | 'end'
}

// Chart tooltip configuration
interface ChartTooltip {
  enabled?: boolean
  formatter?: (value: number, name: string) => string
}

// Common chart configuration
interface ChartConfig {
  title?: string
  xAxis?: ChartAxis
  yAxis?: ChartAxis
  legend?: ChartLegend
  tooltip?: ChartTooltip
  responsive?: boolean
  maintainAspectRatio?: boolean
  height?: number
  width?: number | string
  colors?: string[]
}

// Bar chart specific props
interface BarChartProps {
  data: ChartDataPoint[]
  xKey: string
  yKeys: string[]
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  colors?: string[]
  height?: number
  width?: number | string
  className?: string
  showLegend?: boolean
  showGrid?: boolean
  stacked?: boolean
}

// Line chart specific props
interface LineChartProps {
  data: ChartDataPoint[]
  xKey: string
  yKeys: string[]
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  colors?: string[]
  height?: number
  width?: number | string
  className?: string
  showLegend?: boolean
  showGrid?: boolean
  showDots?: boolean
  curved?: boolean
}

// Chart type enum
type ChartType = 'bar' | 'line'

// Chart JSON format (what AI will generate)
interface ChartJSON {
  type: ChartType
  data: ChartDataPoint[]
  config?: {
    title?: string
    xKey: string
    yKeys: string[]
    xAxisLabel?: string
    yAxisLabel?: string
    colors?: string[]
    height?: number
    width?: number | string
    showLegend?: boolean
    showGrid?: boolean
    stacked?: boolean
    showDots?: boolean
    curved?: boolean
  }
}

// ChartRenderer props
interface ChartRendererProps {
  chartData: string | ChartJSON
  className?: string
}

// HTML element props for chart containers
type ChartContainerProps = DetailedHTMLProps<
  HTMLAttributes<HTMLDivElement>,
  HTMLDivElement
>

type ChartTitleProps = DetailedHTMLProps<
  HTMLAttributes<HTMLHeadingElement>,
  HTMLHeadingElement
>

type ChartWrapperProps = DetailedHTMLProps<
  HTMLAttributes<HTMLDivElement>,
  HTMLDivElement
>

export type {
  ChartDataPoint,
  ChartData,
  ChartDataset,
  ChartAxis,
  ChartLegend,
  ChartTooltip,
  ChartConfig,
  BarChartProps,
  LineChartProps,
  ChartType,
  ChartJSON,
  ChartRendererProps,
  ChartContainerProps,
  ChartTitleProps,
  ChartWrapperProps
}
