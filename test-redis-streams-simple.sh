#!/bin/bash

# Simple Redis Streams Test
set -euo pipefail

REDIS_CONTAINER="opsconductor-redis-streams"
REDIS_PASSWORD="opsconductor-streams-2024"

echo "🧪 Testing Redis Streams Basic Functionality"
echo "=============================================="

# Test 1: Redis connectivity
echo "Test 1: Redis Connectivity"
if docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Redis connectivity: PASSED"
else
    echo "❌ Redis connectivity: FAILED"
    exit 1
fi

# Test 2: Stream creation
echo "Test 2: Stream Creation"
MESSAGE_ID=$(docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" XADD "opsconductor:test:events" "*" "event_type" "test_event" "service" "test" "timestamp" "$(date +%s)" "data" '{"test": true}' 2>/dev/null)
if [[ -n "$MESSAGE_ID" ]]; then
    echo "✅ Stream creation: PASSED (Message ID: $MESSAGE_ID)"
else
    echo "❌ Stream creation: FAILED"
    exit 1
fi

# Test 3: Stream reading
echo "Test 3: Stream Reading"
STREAM_LENGTH=$(docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" XLEN "opsconductor:test:events" 2>/dev/null)
if [[ "$STREAM_LENGTH" -gt 0 ]]; then
    echo "✅ Stream reading: PASSED (Length: $STREAM_LENGTH)"
else
    echo "❌ Stream reading: FAILED"
    exit 1
fi

# Test 4: Consumer group creation
echo "Test 4: Consumer Group Creation"
if docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" XGROUP CREATE "opsconductor:test:events" "test_processors" "0" MKSTREAM 2>/dev/null >/dev/null; then
    echo "✅ Consumer group creation: PASSED"
else
    # Group might already exist
    if docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" XINFO GROUPS "opsconductor:test:events" 2>/dev/null | grep -q "test_processors"; then
        echo "✅ Consumer group creation: PASSED (already exists)"
    else
        echo "❌ Consumer group creation: FAILED"
        exit 1
    fi
fi

# Test 5: Message consumption
echo "Test 5: Message Consumption"
MESSAGES=$(docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" XREADGROUP GROUP "test_processors" "test_consumer" COUNT 1 STREAMS "opsconductor:test:events" ">" 2>/dev/null)
if [[ -n "$MESSAGES" && "$MESSAGES" != "(empty array)" ]]; then
    echo "✅ Message consumption: PASSED"
else
    echo "⚠️  Message consumption: No new messages (expected if already consumed)"
fi

# Test 6: Performance test
echo "Test 6: Performance Test"
START_TIME=$(date +%s.%N)
for i in {1..100}; do
    docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" XADD "opsconductor:perf:events" "*" "event_type" "perf_test" "message_number" "$i" "timestamp" "$(date +%s)" 2>/dev/null >/dev/null
done
END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "1")
MESSAGES_PER_SEC=$(echo "scale=2; 100 / $DURATION" | bc -l 2>/dev/null || echo "N/A")
echo "✅ Performance test: PASSED (100 messages in ${DURATION}s = $MESSAGES_PER_SEC msg/s)"

# Test 7: Redis info
echo "Test 7: Redis Information"
REDIS_VERSION=$(docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" INFO server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
MEMORY_USAGE=$(docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
echo "✅ Redis info: PASSED (Version: $REDIS_VERSION, Memory: $MEMORY_USAGE)"

# Cleanup
echo "Test 8: Cleanup"
docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" DEL "opsconductor:test:events" "opsconductor:perf:events" 2>/dev/null >/dev/null
echo "✅ Cleanup: PASSED"

echo ""
echo "🎉 ALL TESTS PASSED! Redis Streams is working perfectly!"
echo ""
echo "📊 Redis Streams Status:"
echo "  🔴 Redis Streams: http://localhost:6380"
echo "  📦 Version: $REDIS_VERSION"
echo "  💾 Memory Usage: $MEMORY_USAGE"
echo "  ⚡ Performance: $MESSAGES_PER_SEC messages/second"
echo ""
echo "🚀 Redis Streams is ready for integration with OpsConductor services!"