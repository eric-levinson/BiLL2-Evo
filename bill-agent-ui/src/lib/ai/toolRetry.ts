/**
 * Retry configuration options for exponential backoff
 */
export interface RetryOptions {
  /**
   * Maximum number of retry attempts (default: 3)
   */
  maxAttempts?: number
  /**
   * Initial delay in milliseconds before first retry (default: 1000ms)
   */
  initialDelayMs?: number
  /**
   * Multiplier for exponential backoff (default: 2)
   * Each retry delay = previous delay * backoffMultiplier
   */
  backoffMultiplier?: number
  /**
   * Optional function to determine if an error should trigger a retry
   * Returns true to retry, false to throw immediately
   */
  shouldRetry?: (error: unknown, attempt: number) => boolean
  /**
   * Optional callback invoked before each retry attempt
   */
  onRetry?: (error: unknown, attempt: number, delayMs: number) => void
}

/**
 * Error thrown when all retry attempts are exhausted
 */
export class RetryExhaustedError extends Error {
  constructor(
    public readonly lastError: unknown,
    public readonly attempts: number
  ) {
    super(
      `All ${attempts} retry attempts exhausted. Last error: ${
        lastError instanceof Error ? lastError.message : String(lastError)
      }`
    )
    this.name = 'RetryExhaustedError'
  }
}

/**
 * Executes an async function with exponential backoff retry logic
 *
 * Default behavior:
 * - Attempt 1: Executes immediately
 * - Attempt 2: Retries after 1s delay
 * - Attempt 3: Retries after 2s delay
 * - Attempt 4: Retries after 4s delay
 *
 * @param fn - Async function to execute with retry logic
 * @param options - Retry configuration options
 * @returns Promise resolving to the function's return value
 * @throws {RetryExhaustedError} When all retry attempts fail
 *
 * @example
 * ```ts
 * const result = await retryWithBackoff(
 *   async () => await fetchDataFromAPI(),
 *   {
 *     maxAttempts: 3,
 *     initialDelayMs: 1000,
 *     backoffMultiplier: 2,
 *     onRetry: (error, attempt, delay) => {
 *       console.log(`Retry attempt ${attempt} after ${delay}ms: ${error}`)
 *     }
 *   }
 * )
 * ```
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  // Read configuration from environment variables with fallback to options or defaults
  const maxAttempts =
    options.maxAttempts ?? parseInt(process.env.RETRY_MAX_ATTEMPTS || '3', 10)
  const initialDelayMs =
    options.initialDelayMs ??
    parseInt(process.env.RETRY_INITIAL_DELAY_MS || '1000', 10)
  const backoffMultiplier =
    options.backoffMultiplier ??
    parseFloat(process.env.RETRY_BACKOFF_MULTIPLIER || '2')

  const shouldRetry = options.shouldRetry ?? (() => true)
  const onRetry = options.onRetry

  let lastError: unknown

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      // Execute the function
      return await fn()
    } catch (error) {
      lastError = error

      // Check if we should retry this error
      if (!shouldRetry(error, attempt)) {
        throw error
      }

      // If this was the last attempt, throw RetryExhaustedError
      if (attempt === maxAttempts) {
        throw new RetryExhaustedError(lastError, maxAttempts)
      }

      // Calculate exponential backoff delay
      // Attempt 1 -> delay 0 (no delay before first retry)
      // Attempt 2 -> delay = initialDelayMs * multiplier^0 = 1000ms
      // Attempt 3 -> delay = initialDelayMs * multiplier^1 = 2000ms
      // Attempt 4 -> delay = initialDelayMs * multiplier^2 = 4000ms
      const delayMs = initialDelayMs * Math.pow(backoffMultiplier, attempt - 1)

      // Invoke retry callback if provided
      if (onRetry) {
        onRetry(error, attempt, delayMs)
      }

      // Wait before next retry
      await new Promise((resolve) => setTimeout(resolve, delayMs))
    }
  }

  // This should never be reached due to the throw in the last iteration
  // but TypeScript needs this to satisfy the return type
  throw new RetryExhaustedError(lastError, maxAttempts)
}

/**
 * Default retry predicate for common network and timeout errors
 * Retries on:
 * - Network errors (ECONNREFUSED, ETIMEDOUT, ENOTFOUND, etc.)
 * - HTTP 5xx errors (server errors)
 * - HTTP 429 (rate limit - should be retried with backoff)
 * - Timeout errors
 *
 * Does NOT retry on:
 * - HTTP 4xx errors (except 429) - these are client errors that won't succeed on retry
 * - Validation errors
 *
 * @param error - The error to check
 * @returns true if the error should trigger a retry
 */
export function isRetryableError(error: unknown): boolean {
  if (!error) return false

  // Check for Error instances
  if (error instanceof Error) {
    const message = error.message.toLowerCase()

    // Network errors (check message text)
    if (
      message.includes('econnrefused') ||
      message.includes('etimedout') ||
      message.includes('enotfound') ||
      message.includes('econnreset') ||
      message.includes('network') ||
      message.includes('timeout') ||
      message.includes('fetch failed')
    ) {
      return true
    }

    // Check error.cause chain (Node.js fetch wraps network errors in cause)
    if ('cause' in error && error.cause) {
      const cause = error.cause as Record<string, unknown>
      // Check for error codes like ECONNREFUSED, ETIMEDOUT, etc.
      if (
        typeof cause.code === 'string' &&
        ['ECONNREFUSED', 'ETIMEDOUT', 'ENOTFOUND', 'ECONNRESET'].includes(
          cause.code
        )
      ) {
        return true
      }
      // Recurse into cause if it's an Error
      if (cause instanceof Error) {
        return isRetryableError(cause)
      }
    }
  }

  // Check for HTTP errors (if error has a status property)
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const status = (error as { status: number }).status
    // Retry on 5xx (server errors) and 429 (rate limit)
    return status >= 500 || status === 429
  }

  // Default to not retrying unknown errors
  return false
}
