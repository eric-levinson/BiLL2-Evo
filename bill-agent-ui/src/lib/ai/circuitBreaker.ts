/**
 * Circuit breaker state enumeration
 */
export enum CircuitState {
  /**
   * Circuit is closed - requests flow normally
   */
  CLOSED = 'CLOSED',
  /**
   * Circuit is open - requests are blocked, service is considered unavailable
   */
  OPEN = 'OPEN',
  /**
   * Circuit is half-open - testing if service has recovered with a single request
   */
  HALF_OPEN = 'HALF_OPEN',
}

/**
 * Configuration options for circuit breaker
 */
export interface CircuitBreakerOptions {
  /**
   * Number of consecutive failures before opening the circuit (default: 5)
   */
  failureThreshold?: number
  /**
   * Time in milliseconds to wait before attempting to close the circuit (default: 60000ms = 60s)
   */
  resetTimeoutMs?: number
  /**
   * Optional callback invoked when circuit state changes
   */
  onStateChange?: (
    serviceName: string,
    oldState: CircuitState,
    newState: CircuitState
  ) => void
}

/**
 * Error thrown when a request is made while circuit is open
 */
export class CircuitBreakerOpenError extends Error {
  constructor(
    public readonly serviceName: string,
    public readonly resetAt: Date
  ) {
    super(
      `Circuit breaker is OPEN for service "${serviceName}". Service is temporarily unavailable. Will retry after ${resetAt.toISOString()}`
    )
    this.name = 'CircuitBreakerOpenError'
  }
}

/**
 * Circuit breaker implementation for protecting external service calls
 *
 * The circuit breaker prevents cascading failures by tracking service health:
 * - CLOSED: Normal operation, requests flow through
 * - OPEN: Service is failing, requests are blocked immediately
 * - HALF_OPEN: Testing if service has recovered with a single request
 *
 * State transitions:
 * - CLOSED -> OPEN: After failureThreshold consecutive failures
 * - OPEN -> HALF_OPEN: After resetTimeoutMs has elapsed
 * - HALF_OPEN -> CLOSED: If test request succeeds
 * - HALF_OPEN -> OPEN: If test request fails
 *
 * @example
 * ```ts
 * const breaker = new CircuitBreaker({ failureThreshold: 5, resetTimeoutMs: 60000 })
 *
 * try {
 *   await breaker.execute('mcp-server', async () => {
 *     return await mcpClient.callTool('get_player_info', { name: 'Patrick Mahomes' })
 *   })
 * } catch (error) {
 *   if (error instanceof CircuitBreakerOpenError) {
 *     console.log('Service is down, showing cached data or fallback')
 *   }
 * }
 * ```
 */
export class CircuitBreaker {
  private readonly failureThreshold: number
  private readonly resetTimeoutMs: number
  private readonly onStateChange?: (
    serviceName: string,
    oldState: CircuitState,
    newState: CircuitState
  ) => void

  /**
   * Map of service name to circuit state
   */
  private readonly circuits = new Map<
    string,
    {
      state: CircuitState
      consecutiveFailures: number
      lastFailureTime: number | null
      nextAttemptTime: number | null
    }
  >()

  constructor(options: CircuitBreakerOptions = {}) {
    // Read configuration from environment variables with fallback to options or defaults
    this.failureThreshold =
      options.failureThreshold ??
      parseInt(process.env.CIRCUIT_BREAKER_THRESHOLD || '5', 10)
    this.resetTimeoutMs =
      options.resetTimeoutMs ??
      parseInt(process.env.CIRCUIT_BREAKER_TIMEOUT_MS || '60000', 10)
    this.onStateChange = options.onStateChange
  }

  /**
   * Get or initialize circuit state for a service
   */
  private getCircuit(serviceName: string) {
    if (!this.circuits.has(serviceName)) {
      this.circuits.set(serviceName, {
        state: CircuitState.CLOSED,
        consecutiveFailures: 0,
        lastFailureTime: null,
        nextAttemptTime: null,
      })
    }
    return this.circuits.get(serviceName)!
  }

  /**
   * Get the current state of a circuit
   */
  public getState(serviceName: string): CircuitState {
    const circuit = this.getCircuit(serviceName)

    // Check if we should transition from OPEN to HALF_OPEN
    if (
      circuit.state === CircuitState.OPEN &&
      circuit.nextAttemptTime !== null &&
      Date.now() >= circuit.nextAttemptTime
    ) {
      this.transitionState(serviceName, CircuitState.HALF_OPEN)
    }

    return circuit.state
  }

  /**
   * Transition circuit to a new state
   */
  private transitionState(
    serviceName: string,
    newState: CircuitState
  ): void {
    const circuit = this.getCircuit(serviceName)
    const oldState = circuit.state

    if (oldState === newState) return

    circuit.state = newState

    // Reset nextAttemptTime when entering HALF_OPEN or CLOSED
    if (newState === CircuitState.HALF_OPEN || newState === CircuitState.CLOSED) {
      circuit.nextAttemptTime = null
    }

    // Reset consecutive failures when entering CLOSED
    if (newState === CircuitState.CLOSED) {
      circuit.consecutiveFailures = 0
    }

    // Invoke state change callback if provided
    if (this.onStateChange) {
      this.onStateChange(serviceName, oldState, newState)
    }
  }

  /**
   * Record a successful request
   */
  private recordSuccess(serviceName: string): void {
    const circuit = this.getCircuit(serviceName)

    // If we're in HALF_OPEN and the request succeeded, close the circuit
    if (circuit.state === CircuitState.HALF_OPEN) {
      this.transitionState(serviceName, CircuitState.CLOSED)
    }

    // Reset failure count on success
    circuit.consecutiveFailures = 0
    circuit.lastFailureTime = null
  }

  /**
   * Record a failed request
   */
  private recordFailure(serviceName: string): void {
    const circuit = this.getCircuit(serviceName)
    const now = Date.now()

    circuit.consecutiveFailures++
    circuit.lastFailureTime = now

    // If we're in HALF_OPEN and the request failed, reopen the circuit
    if (circuit.state === CircuitState.HALF_OPEN) {
      this.transitionState(serviceName, CircuitState.OPEN)
      circuit.nextAttemptTime = now + this.resetTimeoutMs
      return
    }

    // If we've hit the failure threshold, open the circuit
    if (
      circuit.state === CircuitState.CLOSED &&
      circuit.consecutiveFailures >= this.failureThreshold
    ) {
      this.transitionState(serviceName, CircuitState.OPEN)
      circuit.nextAttemptTime = now + this.resetTimeoutMs
    }
  }

  /**
   * Execute a function with circuit breaker protection
   *
   * @param serviceName - Unique identifier for the service (e.g., 'mcp-server', 'sleeper-api')
   * @param fn - Async function to execute
   * @returns Promise resolving to the function's return value
   * @throws {CircuitBreakerOpenError} When circuit is OPEN and service is unavailable
   * @throws Original error if the function fails
   */
  public async execute<T>(
    serviceName: string,
    fn: () => Promise<T>
  ): Promise<T> {
    const currentState = this.getState(serviceName)

    // Block requests if circuit is OPEN
    if (currentState === CircuitState.OPEN) {
      const circuit = this.getCircuit(serviceName)
      const resetAt = circuit.nextAttemptTime
        ? new Date(circuit.nextAttemptTime)
        : new Date(Date.now() + this.resetTimeoutMs)
      throw new CircuitBreakerOpenError(serviceName, resetAt)
    }

    try {
      // Execute the function
      const result = await fn()
      this.recordSuccess(serviceName)
      return result
    } catch (error) {
      this.recordFailure(serviceName)
      throw error
    }
  }

  /**
   * Manually reset a circuit to CLOSED state
   * Useful for administrative overrides or testing
   */
  public reset(serviceName: string): void {
    const circuit = this.getCircuit(serviceName)
    circuit.state = CircuitState.CLOSED
    circuit.consecutiveFailures = 0
    circuit.lastFailureTime = null
    circuit.nextAttemptTime = null
  }

  /**
   * Get circuit statistics for monitoring
   */
  public getStats(serviceName: string) {
    const circuit = this.getCircuit(serviceName)
    return {
      state: circuit.state,
      consecutiveFailures: circuit.consecutiveFailures,
      lastFailureTime: circuit.lastFailureTime
        ? new Date(circuit.lastFailureTime)
        : null,
      nextAttemptTime: circuit.nextAttemptTime
        ? new Date(circuit.nextAttemptTime)
        : null,
    }
  }
}
