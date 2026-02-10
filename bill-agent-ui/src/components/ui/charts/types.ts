// Base data point structure for all charts
interface ChartDataPoint {
  [key: string]: string | number | null | undefined
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

export type {
  ChartDataPoint,
  BarChartProps,
  LineChartProps,
  ChartType,
  ChartJSON,
  ChartRendererProps
}
