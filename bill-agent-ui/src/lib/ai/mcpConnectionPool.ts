import { createMCPClient, type MCPClient } from '@ai-sdk/mcp'
import { retryWithBackoff, isRetryableError } from './toolRetry'
import { CircuitBreaker } from './circuitBreaker'

/**
 * Connection state enumeration
 */
export enum ConnectionState {
  /**
   * Connection is idle and available for use
   */
  IDLE = 'IDLE',
  /**
   * Connection is currently in use
   */
  ACTIVE = 'ACTIVE',
  /**
   * Connection is unhealthy and should be replaced
   */
  UNHEALTHY = 'UNHEALTHY'
}

/**
 * Pooled connection metadata
 */
interface PooledConnection {
  /**
   * Unique identifier for this connection
   */
  id: string
  /**
   * MCP client instance
   */
  client: MCPClient
  /**
   * Current state of the connection
   */
  state: ConnectionState
  /**
   * Timestamp of last use (for idle timeout)
   */
  lastUsedAt: number
  /**
   * Timestamp when connection was created
   */
  createdAt: number
  /**
   * Number of times this connection has been acquired
   */
  usageCount: number
}

/**
 * Configuration options for connection pool
 */
export interface MCPConnectionPoolOptions {
  /**
   * MCP server URL to connect to
   */
  serverUrl: string
  /**
   * Minimum number of connections to maintain (default: 2)
   */
  minConnections?: number
  /**
   * Maximum number of connections allowed (default: 5)
   */
  maxConnections?: number
  /**
   * Time in milliseconds before idle connections are closed (default: 300000ms = 5 minutes)
   */
  idleTimeoutMs?: number
  /**
   * Circuit breaker instance for connection health management
   */
  circuitBreaker?: CircuitBreaker
  /**
   * Optional callback invoked when a connection is created
   */
  onConnectionCreated?: (connectionId: string) => void
  /**
   * Optional callback invoked when a connection is closed
   */
  onConnectionClosed?: (connectionId: string, reason: string) => void
}

/**
 * Error thrown when connection pool is exhausted and cannot create new connections
 */
export class ConnectionPoolExhaustedError extends Error {
  constructor(public readonly maxConnections: number) {
    super(
      `Connection pool exhausted: all ${maxConnections} connections are in use. Consider increasing MCP_POOL_MAX_CONNECTIONS.`
    )
    this.name = 'ConnectionPoolExhaustedError'
  }
}

/**
 * MCP client connection pool for reducing per-request connection overhead
 *
 * The connection pool maintains persistent MCP client connections to eliminate
 * the 50-100ms overhead of establishing new connections for each request.
 *
 * Features:
 * - Connection reuse across requests
 * - Automatic connection health monitoring
 * - Idle connection cleanup
 * - Integration with circuit breaker for fault tolerance
 * - Configurable pool size limits
 *
 * State management:
 * - IDLE: Connection available for use
 * - ACTIVE: Connection currently in use
 * - UNHEALTHY: Connection failed health check, should be replaced
 *
 * @example
 * ```ts
 * const pool = new MCPConnectionPool({
 *   serverUrl: 'http://localhost:8000/mcp/',
 *   minConnections: 2,
 *   maxConnections: 5,
 *   circuitBreaker: mcpCircuitBreaker
 * })
 *
 * // Acquire a connection
 * const client = await pool.acquire()
 * try {
 *   const tools = await client.listTools()
 *   // Use the client...
 * } finally {
 *   // Always release back to pool
 *   await pool.release(client)
 * }
 * ```
 */
export class MCPConnectionPool {
  private readonly serverUrl: string
  private readonly minConnections: number
  private readonly maxConnections: number
  private readonly idleTimeoutMs: number
  private readonly circuitBreaker?: CircuitBreaker
  private readonly onConnectionCreated?: (connectionId: string) => void
  private readonly onConnectionClosed?: (
    connectionId: string,
    reason: string
  ) => void

  /**
   * Map of connection ID to pooled connection
   */
  private readonly connections = new Map<string, PooledConnection>()

  /**
   * Counter for generating unique connection IDs
   */
  private connectionIdCounter = 0

  /**
   * Interval handle for idle connection cleanup
   */
  private idleCheckInterval?: NodeJS.Timeout

  /**
   * Flag to track if pool is initializing connections
   */
  private isInitializing = false

  constructor(options: MCPConnectionPoolOptions) {
    this.serverUrl = options.serverUrl

    // Read configuration from environment variables with fallback to options or defaults
    this.minConnections =
      options.minConnections ?? parseInt(process.env.MCP_POOL_SIZE || '2', 10)
    this.maxConnections =
      options.maxConnections ??
      parseInt(process.env.MCP_POOL_MAX_CONNECTIONS || '5', 10)
    this.idleTimeoutMs =
      options.idleTimeoutMs ??
      parseInt(process.env.MCP_POOL_IDLE_TIMEOUT_MS || '300000', 10)

    this.circuitBreaker = options.circuitBreaker
    this.onConnectionCreated = options.onConnectionCreated
    this.onConnectionClosed = options.onConnectionClosed

    // Validate configuration
    if (this.minConnections < 0) {
      throw new Error('minConnections must be >= 0')
    }
    if (this.maxConnections < this.minConnections) {
      throw new Error('maxConnections must be >= minConnections')
    }

    // Start idle connection cleanup timer
    this.startIdleConnectionCleanup()
  }

  /**
   * Generate a unique connection ID
   */
  private generateConnectionId(): string {
    return `mcp-conn-${++this.connectionIdCounter}`
  }

  /**
   * Create a new MCP client connection
   */
  private async createConnection(): Promise<PooledConnection> {
    const connectionId = this.generateConnectionId()
    const now = Date.now()

    console.log(`[MCP Pool] Creating new connection: ${connectionId}`)

    // Use circuit breaker and retry logic if provided
    const createClient = async () => {
      return await createMCPClient({
        transport: {
          type: 'http',
          url: this.serverUrl
        }
      })
    }

    let client: MCPClient
    if (this.circuitBreaker) {
      client = await this.circuitBreaker.execute('mcp-server', async () => {
        return await retryWithBackoff(createClient, {
          shouldRetry: isRetryableError,
          onRetry: (error, attempt, delayMs) => {
            const errorMsg =
              error instanceof Error ? error.message : String(error)
            console.error(
              `[MCP Pool] Connection creation retry attempt ${attempt} after ${delayMs}ms: ${errorMsg}`
            )
          }
        })
      })
    } else {
      client = await createClient()
    }

    const connection: PooledConnection = {
      id: connectionId,
      client,
      state: ConnectionState.IDLE,
      lastUsedAt: now,
      createdAt: now,
      usageCount: 0
    }

    this.connections.set(connectionId, connection)

    if (this.onConnectionCreated) {
      this.onConnectionCreated(connectionId)
    }

    console.log(
      `[MCP Pool] Connection created: ${connectionId} (total: ${this.connections.size}/${this.maxConnections})`
    )

    return connection
  }

  /**
   * Close a connection and remove it from the pool
   */
  private async closeConnection(
    connectionId: string,
    reason: string
  ): Promise<void> {
    const connection = this.connections.get(connectionId)
    if (!connection) return

    console.log(`[MCP Pool] Closing connection: ${connectionId} (${reason})`)

    try {
      await connection.client.close()
    } catch (error) {
      console.error(
        `[MCP Pool] Error closing connection ${connectionId}:`,
        error
      )
    }

    this.connections.delete(connectionId)

    if (this.onConnectionClosed) {
      this.onConnectionClosed(connectionId, reason)
    }

    console.log(
      `[MCP Pool] Connection closed: ${connectionId} (remaining: ${this.connections.size})`
    )
  }

  /**
   * Find an idle connection or create a new one
   */
  private async getOrCreateConnection(): Promise<PooledConnection> {
    // First, try to find an idle connection
    for (const connection of Array.from(this.connections.values())) {
      if (connection.state === ConnectionState.IDLE) {
        console.log(
          `[MCP Pool] Reusing idle connection: ${connection.id} (age: ${Date.now() - connection.createdAt}ms, uses: ${connection.usageCount})`
        )
        return connection
      }
    }

    // No idle connections available, create a new one if under max limit
    if (this.connections.size < this.maxConnections) {
      return await this.createConnection()
    }

    // Pool is exhausted - all connections are active
    throw new ConnectionPoolExhaustedError(this.maxConnections)
  }

  /**
   * Initialize minimum number of connections
   * This is called lazily on first acquire() to avoid blocking module initialization
   */
  private async initializePool(): Promise<void> {
    if (this.isInitializing || this.connections.size >= this.minConnections) {
      return
    }

    this.isInitializing = true
    console.log(
      `[MCP Pool] Initializing pool with ${this.minConnections} connections`
    )

    try {
      // Create connections in parallel up to minConnections
      const connectionsToCreate = this.minConnections - this.connections.size
      const creationPromises = Array.from({ length: connectionsToCreate }, () =>
        this.createConnection()
      )

      await Promise.all(creationPromises)
      console.log(
        `[MCP Pool] Pool initialized with ${this.minConnections} connections`
      )
    } catch (error) {
      console.error('[MCP Pool] Error initializing pool:', error)
      // Don't throw - pool can still work with fewer connections
    } finally {
      this.isInitializing = false
    }
  }

  /**
   * Acquire a connection from the pool
   *
   * @returns Promise resolving to an MCP client instance
   * @throws {ConnectionPoolExhaustedError} When all connections are in use and max limit is reached
   * @throws {CircuitBreakerOpenError} When circuit breaker is open
   * @throws {RetryExhaustedError} When connection creation fails after retries
   */
  public async acquire(): Promise<MCPClient> {
    const acquireStart = performance.now()

    // Initialize pool on first acquire (lazy initialization)
    if (this.connections.size === 0 && !this.isInitializing) {
      await this.initializePool()
    }

    // Track whether we're reusing an existing connection
    const connectionsBefore = this.connections.size
    const connection = await this.getOrCreateConnection()
    const wasCached = this.connections.size === connectionsBefore

    // Mark connection as active
    connection.state = ConnectionState.ACTIVE
    connection.lastUsedAt = Date.now()
    connection.usageCount++

    const acquireEnd = performance.now()
    const acquisitionTime = (acquireEnd - acquireStart).toFixed(2)

    console.log(
      `[MCP Pool] Connection acquired in ${acquisitionTime}ms (cached: ${wasCached}) - ${connection.id} (active: ${this.getActiveCount()}/${this.connections.size})`
    )

    return connection.client
  }

  /**
   * Release a connection back to the pool
   *
   * @param client - MCP client instance to release
   * @param markUnhealthy - Optional flag to mark connection as unhealthy (will be closed and removed)
   */
  public async release(
    client: MCPClient,
    markUnhealthy = false
  ): Promise<void> {
    // Find the connection by client instance
    let connectionId: string | null = null
    for (const [id, conn] of Array.from(this.connections.entries())) {
      if (conn.client === client) {
        connectionId = id
        break
      }
    }

    if (!connectionId) {
      console.warn('[MCP Pool] Attempted to release unknown connection')
      return
    }

    const connection = this.connections.get(connectionId)!

    if (markUnhealthy) {
      connection.state = ConnectionState.UNHEALTHY
      await this.closeConnection(connectionId, 'marked unhealthy')
      return
    }

    // Return connection to idle state
    connection.state = ConnectionState.IDLE
    connection.lastUsedAt = Date.now()

    console.log(
      `[MCP Pool] Connection released: ${connectionId} (idle: ${this.getIdleCount()}/${this.connections.size})`
    )
  }

  /**
   * Start periodic cleanup of idle connections
   */
  private startIdleConnectionCleanup(): void {
    // Check for idle connections every minute
    const checkInterval = 60000 // 1 minute

    this.idleCheckInterval = setInterval(() => {
      this.cleanupIdleConnections()
    }, checkInterval)

    // Don't prevent process from exiting
    if (this.idleCheckInterval.unref) {
      this.idleCheckInterval.unref()
    }
  }

  /**
   * Clean up connections that have been idle for too long
   */
  private async cleanupIdleConnections(): Promise<void> {
    const now = Date.now()
    const connectionsToClose: string[] = []

    // Find idle connections that exceed timeout
    for (const [id, connection] of Array.from(this.connections.entries())) {
      if (
        connection.state === ConnectionState.IDLE &&
        now - connection.lastUsedAt > this.idleTimeoutMs &&
        this.connections.size > this.minConnections
      ) {
        connectionsToClose.push(id)
      }
    }

    // Close idle connections
    for (const id of connectionsToClose) {
      await this.closeConnection(id, 'idle timeout')
    }

    if (connectionsToClose.length > 0) {
      console.log(
        `[MCP Pool] Cleaned up ${connectionsToClose.length} idle connections`
      )
    }
  }

  /**
   * Get the number of active connections
   */
  private getActiveCount(): number {
    let count = 0
    for (const connection of Array.from(this.connections.values())) {
      if (connection.state === ConnectionState.ACTIVE) {
        count++
      }
    }
    return count
  }

  /**
   * Get the number of idle connections
   */
  private getIdleCount(): number {
    let count = 0
    for (const connection of Array.from(this.connections.values())) {
      if (connection.state === ConnectionState.IDLE) {
        count++
      }
    }
    return count
  }

  /**
   * Get pool statistics for monitoring
   */
  public getStats() {
    return {
      totalConnections: this.connections.size,
      activeConnections: this.getActiveCount(),
      idleConnections: this.getIdleCount(),
      minConnections: this.minConnections,
      maxConnections: this.maxConnections,
      idleTimeoutMs: this.idleTimeoutMs,
      connections: Array.from(this.connections.values()).map((conn) => ({
        id: conn.id,
        state: conn.state,
        age: Date.now() - conn.createdAt,
        idleTime: Date.now() - conn.lastUsedAt,
        usageCount: conn.usageCount
      }))
    }
  }

  /**
   * Close all connections and shut down the pool
   * Should be called when the application is shutting down
   */
  public async shutdown(): Promise<void> {
    console.log('[MCP Pool] Shutting down connection pool')

    // Stop idle connection cleanup
    if (this.idleCheckInterval) {
      clearInterval(this.idleCheckInterval)
    }

    // Close all connections
    const closePromises = Array.from(this.connections.keys()).map((id) =>
      this.closeConnection(id, 'pool shutdown')
    )

    await Promise.all(closePromises)

    console.log('[MCP Pool] Pool shutdown complete')
  }
}
