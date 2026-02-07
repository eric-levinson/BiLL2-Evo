/**
 * Configuration Verification Test for Retry Logic and Circuit Breaker
 *
 * Tests that all environment variables properly override default configuration:
 * - RETRY_MAX_ATTEMPTS
 * - RETRY_INITIAL_DELAY_MS
 * - RETRY_BACKOFF_MULTIPLIER
 * - CIRCUIT_BREAKER_THRESHOLD
 * - CIRCUIT_BREAKER_TIMEOUT_MS
 */

const { retryWithBackoff, RetryExhaustedError } = require('./src/lib/ai/toolRetry.ts');
const { CircuitBreaker, CircuitState, CircuitBreakerOpenError } = require('./src/lib/ai/circuitBreaker.ts');

// Helper to measure execution time
function measureTime(fn) {
  const start = Date.now();
  return fn().finally(() => {
    const duration = Date.now() - start;
    return duration;
  });
}

// Helper to create a function that always fails
function createAlwaysFailingFn() {
  let callCount = 0;
  return async () => {
    callCount++;
    throw new Error(`Simulated failure (call ${callCount})`);
  };
}

// Helper to verify timing accuracy
function verifyTiming(actual, expected, tolerance = 50) {
  const diff = Math.abs(actual - expected);
  const accuracy = ((expected - diff) / expected) * 100;
  return {
    actual,
    expected,
    diff,
    accuracy: accuracy.toFixed(1),
    pass: diff <= tolerance
  };
}

// Test 1: RETRY_MAX_ATTEMPTS
async function testRetryMaxAttempts() {
  console.log('\n=== Test 1: RETRY_MAX_ATTEMPTS ===');

  // Set environment variable
  process.env.RETRY_MAX_ATTEMPTS = '2';

  const failFn = createAlwaysFailingFn();
  let attempts = 0;

  try {
    await retryWithBackoff(failFn, {
      onRetry: (error, attempt) => {
        attempts = attempt;
        console.log(`  Retry attempt ${attempt}`);
      }
    });
  } catch (error) {
    if (error instanceof RetryExhaustedError) {
      console.log(`  ✓ RetryExhaustedError thrown after ${error.attempts} attempts`);

      if (error.attempts === 2) {
        console.log('  ✓ PASS: RETRY_MAX_ATTEMPTS=2 correctly limited retries to 2 attempts');
        return true;
      } else {
        console.log(`  ✗ FAIL: Expected 2 attempts, got ${error.attempts}`);
        return false;
      }
    }
  }

  console.log('  ✗ FAIL: Expected RetryExhaustedError to be thrown');
  return false;
}

// Test 2: RETRY_INITIAL_DELAY_MS
async function testRetryInitialDelay() {
  console.log('\n=== Test 2: RETRY_INITIAL_DELAY_MS ===');

  // Set environment variable to 500ms (half of default)
  process.env.RETRY_INITIAL_DELAY_MS = '500';
  process.env.RETRY_MAX_ATTEMPTS = '2';
  process.env.RETRY_BACKOFF_MULTIPLIER = '1'; // No exponential growth for this test

  const expectedDelay = 500; // First retry should be 500ms
  const callTimes = [];

  const failFn = async () => {
    callTimes.push(Date.now());
    throw new Error('Simulated failure');
  };

  try {
    await retryWithBackoff(failFn, {
      onRetry: (error, attempt, delayMs) => {
        console.log(`  Retry ${attempt + 1} scheduled with ${delayMs}ms delay`);
      }
    });
  } catch (error) {
    // Calculate actual delay between first and second call
    if (callTimes.length >= 2) {
      const actualDelay = callTimes[1] - callTimes[0];
      console.log(`  First retry delay: ${actualDelay}ms (expected: ${expectedDelay}ms)`);

      const timing = verifyTiming(actualDelay, expectedDelay);
      console.log(`  Timing accuracy: ${timing.accuracy}% (diff: ${timing.diff}ms)`);

      if (timing.pass) {
        console.log('  ✓ PASS: RETRY_INITIAL_DELAY_MS=500 correctly set initial delay to 500ms');
        return true;
      } else {
        console.log(`  ✗ FAIL: Delay off by ${timing.diff}ms (tolerance: 50ms)`);
        return false;
      }
    }
  }

  console.log('  ✗ FAIL: Expected RetryExhaustedError to be thrown');
  return false;
}

// Test 3: RETRY_BACKOFF_MULTIPLIER
async function testRetryBackoffMultiplier() {
  console.log('\n=== Test 3: RETRY_BACKOFF_MULTIPLIER ===');

  // Set multiplier to 3 instead of default 2
  process.env.RETRY_INITIAL_DELAY_MS = '100';
  process.env.RETRY_BACKOFF_MULTIPLIER = '3';
  process.env.RETRY_MAX_ATTEMPTS = '3';

  const expectedDelays = [100, 300]; // 100 * 3^0, 100 * 3^1
  const callTimes = [];

  const failFn = async () => {
    callTimes.push(Date.now());
    throw new Error('Simulated failure');
  };

  try {
    await retryWithBackoff(failFn, {
      onRetry: (error, attempt, delayMs) => {
        console.log(`  Retry ${attempt + 1} scheduled with ${delayMs}ms delay`);
      }
    });
  } catch (error) {
    // Verify delays between calls
    if (callTimes.length >= 3) {
      const delay1 = callTimes[1] - callTimes[0];
      const delay2 = callTimes[2] - callTimes[1];

      console.log(`  Delay 1: ${delay1}ms (expected: ${expectedDelays[0]}ms)`);
      console.log(`  Delay 2: ${delay2}ms (expected: ${expectedDelays[1]}ms)`);

      const timing1 = verifyTiming(delay1, expectedDelays[0]);
      const timing2 = verifyTiming(delay2, expectedDelays[1]);

      console.log(`  Delay 1 accuracy: ${timing1.accuracy}% (diff: ${timing1.diff}ms)`);
      console.log(`  Delay 2 accuracy: ${timing2.accuracy}% (diff: ${timing2.diff}ms)`);

      if (timing1.pass && timing2.pass) {
        console.log('  ✓ PASS: RETRY_BACKOFF_MULTIPLIER=3 correctly applied 3x exponential backoff');
        return true;
      } else {
        console.log('  ✗ FAIL: Backoff multiplier not correctly applied');
        return false;
      }
    }
  }

  console.log('  ✗ FAIL: Expected RetryExhaustedError to be thrown');
  return false;
}

// Test 4: CIRCUIT_BREAKER_THRESHOLD
async function testCircuitBreakerThreshold() {
  console.log('\n=== Test 4: CIRCUIT_BREAKER_THRESHOLD ===');

  // Set threshold to 3 instead of default 5
  process.env.CIRCUIT_BREAKER_THRESHOLD = '3';
  process.env.CIRCUIT_BREAKER_TIMEOUT_MS = '5000';

  const breaker = new CircuitBreaker({
    onStateChange: (serviceName, oldState, newState) => {
      console.log(`  State transition: ${oldState} -> ${newState}`);
    }
  });

  const failFn = async () => {
    throw new Error('Simulated failure');
  };

  // Initial state should be CLOSED
  if (breaker.getState('test-service') !== CircuitState.CLOSED) {
    console.log('  ✗ FAIL: Initial state should be CLOSED');
    return false;
  }

  // Trigger 3 failures
  for (let i = 1; i <= 3; i++) {
    try {
      await breaker.execute('test-service', failFn);
    } catch (error) {
      console.log(`  Failure ${i} recorded`);
    }
  }

  // Circuit should now be OPEN after 3 failures (threshold = 3)
  const finalState = breaker.getState('test-service');
  if (finalState === CircuitState.OPEN) {
    console.log('  ✓ PASS: CIRCUIT_BREAKER_THRESHOLD=3 correctly opened circuit after 3 failures');
    return true;
  } else {
    console.log(`  ✗ FAIL: Expected circuit to be OPEN, got ${finalState}`);
    return false;
  }
}

// Test 5: CIRCUIT_BREAKER_TIMEOUT_MS
async function testCircuitBreakerTimeout() {
  console.log('\n=== Test 5: CIRCUIT_BREAKER_TIMEOUT_MS ===');

  // Set timeout to 2 seconds instead of default 60 seconds
  process.env.CIRCUIT_BREAKER_THRESHOLD = '2';
  process.env.CIRCUIT_BREAKER_TIMEOUT_MS = '2000';

  const breaker = new CircuitBreaker({
    onStateChange: (serviceName, oldState, newState) => {
      console.log(`  State transition: ${oldState} -> ${newState}`);
    }
  });

  const failFn = async () => {
    throw new Error('Simulated failure');
  };

  // Open the circuit with 2 failures
  for (let i = 1; i <= 2; i++) {
    try {
      await breaker.execute('test-service-2', failFn);
    } catch (error) {
      console.log(`  Failure ${i} recorded`);
    }
  }

  // Verify circuit is OPEN
  if (breaker.getState('test-service-2') !== CircuitState.OPEN) {
    console.log('  ✗ FAIL: Circuit should be OPEN');
    return false;
  }
  console.log('  Circuit is OPEN');

  // Wait 2.1 seconds for auto-reset
  console.log('  Waiting 2.1 seconds for circuit to reset...');
  await new Promise(resolve => setTimeout(resolve, 2100));

  // Circuit should transition to HALF_OPEN
  const state = breaker.getState('test-service-2');
  if (state === CircuitState.HALF_OPEN) {
    console.log('  ✓ PASS: CIRCUIT_BREAKER_TIMEOUT_MS=2000 correctly reset circuit after 2 seconds');
    return true;
  } else {
    console.log(`  ✗ FAIL: Expected circuit to be HALF_OPEN after timeout, got ${state}`);
    return false;
  }
}

// Run all tests
async function runAllTests() {
  console.log('=====================================');
  console.log('Configuration Verification Tests');
  console.log('=====================================');

  const results = [];

  // Clear any existing env vars
  delete process.env.RETRY_MAX_ATTEMPTS;
  delete process.env.RETRY_INITIAL_DELAY_MS;
  delete process.env.RETRY_BACKOFF_MULTIPLIER;
  delete process.env.CIRCUIT_BREAKER_THRESHOLD;
  delete process.env.CIRCUIT_BREAKER_TIMEOUT_MS;

  results.push({ name: 'RETRY_MAX_ATTEMPTS', pass: await testRetryMaxAttempts() });

  // Reset env vars between tests
  delete process.env.RETRY_MAX_ATTEMPTS;
  delete process.env.RETRY_INITIAL_DELAY_MS;
  delete process.env.RETRY_BACKOFF_MULTIPLIER;

  results.push({ name: 'RETRY_INITIAL_DELAY_MS', pass: await testRetryInitialDelay() });

  // Reset env vars
  delete process.env.RETRY_MAX_ATTEMPTS;
  delete process.env.RETRY_INITIAL_DELAY_MS;
  delete process.env.RETRY_BACKOFF_MULTIPLIER;

  results.push({ name: 'RETRY_BACKOFF_MULTIPLIER', pass: await testRetryBackoffMultiplier() });

  // Reset env vars
  delete process.env.CIRCUIT_BREAKER_THRESHOLD;
  delete process.env.CIRCUIT_BREAKER_TIMEOUT_MS;

  results.push({ name: 'CIRCUIT_BREAKER_THRESHOLD', pass: await testCircuitBreakerThreshold() });

  // Reset env vars
  delete process.env.CIRCUIT_BREAKER_THRESHOLD;
  delete process.env.CIRCUIT_BREAKER_TIMEOUT_MS;

  results.push({ name: 'CIRCUIT_BREAKER_TIMEOUT_MS', pass: await testCircuitBreakerTimeout() });

  // Summary
  console.log('\n=====================================');
  console.log('Test Summary');
  console.log('=====================================');

  const passed = results.filter(r => r.pass).length;
  const total = results.length;

  results.forEach(result => {
    const status = result.pass ? '✓ PASS' : '✗ FAIL';
    console.log(`${status}: ${result.name}`);
  });

  console.log(`\nTotal: ${passed}/${total} tests passed`);

  if (passed === total) {
    console.log('\n✓ All configuration environment variables work correctly!');
    process.exit(0);
  } else {
    console.log('\n✗ Some configuration tests failed');
    process.exit(1);
  }
}

// Run tests
runAllTests().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});
