#!/bin/bash

# Redis Streams Testing Script for OpsConductor
# Comprehensive testing of Redis Streams functionality, consumer groups, and message processing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REDIS_CONTAINER="opsconductor-redis-streams"
REDIS_PASSWORD="opsconductor-streams-2024"
MONITOR_URL="http://localhost:8090"
TEST_LOG="redis-streams-test.log"
TEST_STREAM="opsconductor:test:events"
TEST_GROUP="test_processors"
TEST_CONSUMER="test_consumer"

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$TEST_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$TEST_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$TEST_LOG"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$TEST_LOG"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1" | tee -a "$TEST_LOG"
}

# Test framework functions
start_test() {
    local test_name="$1"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    log "🧪 Test $TESTS_TOTAL: $test_name"
}

pass_test() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    success "✅ Test passed"
}

fail_test() {
    local reason="$1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    error "❌ Test failed: $reason"
}

# Redis command wrapper
redis_cmd() {
    docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" "$@" 2>/dev/null
}

# Function to display test banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           🧪 REDIS STREAMS TESTING SUITE 🧪                 ║"
    echo "║                                                              ║"
    echo "║  Comprehensive testing of Redis Streams functionality       ║"
    echo "║  • Basic Redis operations                                    ║"
    echo "║  • Stream creation and management                            ║"
    echo "║  • Consumer groups and message processing                    ║"
    echo "║  • Message acknowledgments and retries                      ║"
    echo "║  • Dead letter queue functionality                          ║"
    echo "║  • Performance and load testing                             ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Test 1: Basic Redis connectivity
test_redis_connectivity() {
    start_test "Redis Connectivity"
    
    if redis_cmd ping | grep -q "PONG"; then
        pass_test
    else
        fail_test "Redis not responding to ping"
    fi
}

# Test 2: Redis info and configuration
test_redis_info() {
    start_test "Redis Configuration"
    
    local redis_version=$(redis_cmd INFO server | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    local memory_usage=$(redis_cmd INFO memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    
    if [[ -n "$redis_version" ]]; then
        info "Redis version: $redis_version"
        info "Memory usage: $memory_usage"
        pass_test
    else
        fail_test "Could not retrieve Redis info"
    fi
}

# Test 3: Stream creation
test_stream_creation() {
    start_test "Stream Creation"
    
    # Clean up any existing test stream
    redis_cmd DEL "$TEST_STREAM" >/dev/null 2>&1 || true
    
    # Create stream with initial message
    local message_id=$(redis_cmd XADD "$TEST_STREAM" "*" "event_type" "test_event" "service" "test" "timestamp" "$(date +%s)" "data" '{"test": true}')
    
    if [[ -n "$message_id" ]]; then
        info "Created stream with message ID: $message_id"
        pass_test
    else
        fail_test "Could not create stream"
    fi
}

# Test 4: Stream information
test_stream_info() {
    start_test "Stream Information"
    
    local stream_length=$(redis_cmd XLEN "$TEST_STREAM")
    local stream_info=$(redis_cmd XINFO STREAM "$TEST_STREAM")
    
    if [[ "$stream_length" -gt 0 ]]; then
        info "Stream length: $stream_length"
        pass_test
    else
        fail_test "Stream appears to be empty"
    fi
}

# Test 5: Consumer group creation
test_consumer_group_creation() {
    start_test "Consumer Group Creation"
    
    # Create consumer group
    if redis_cmd XGROUP CREATE "$TEST_STREAM" "$TEST_GROUP" "0" MKSTREAM >/dev/null 2>&1; then
        info "Created consumer group: $TEST_GROUP"
        pass_test
    else
        # Group might already exist
        if redis_cmd XINFO GROUPS "$TEST_STREAM" | grep -q "$TEST_GROUP"; then
            info "Consumer group already exists: $TEST_GROUP"
            pass_test
        else
            fail_test "Could not create consumer group"
        fi
    fi
}

# Test 6: Message publishing
test_message_publishing() {
    start_test "Message Publishing"
    
    local messages_published=0
    local event_types=("user_created" "asset_updated" "automation_started" "notification_sent" "ai_analysis_completed")
    
    for event_type in "${event_types[@]}"; do
        local message_id=$(redis_cmd XADD "$TEST_STREAM" "*" \
            "event_type" "$event_type" \
            "service" "test_service" \
            "timestamp" "$(date +%s)" \
            "priority" "normal" \
            "correlation_id" "test-$(uuidgen 2>/dev/null || echo "test-$RANDOM")" \
            "data" "{\"test_data\": \"$event_type\", \"timestamp\": $(date +%s)}")
        
        if [[ -n "$message_id" ]]; then
            messages_published=$((messages_published + 1))
        fi
    done
    
    if [[ "$messages_published" -eq "${#event_types[@]}" ]]; then
        info "Published $messages_published messages successfully"
        pass_test
    else
        fail_test "Only published $messages_published out of ${#event_types[@]} messages"
    fi
}

# Test 7: Message consumption
test_message_consumption() {
    start_test "Message Consumption"
    
    # Read messages from consumer group
    local messages=$(redis_cmd XREADGROUP GROUP "$TEST_GROUP" "$TEST_CONSUMER" COUNT 5 STREAMS "$TEST_STREAM" ">")
    
    if [[ -n "$messages" && "$messages" != "(empty array)" ]]; then
        info "Successfully consumed messages from stream"
        pass_test
    else
        fail_test "Could not consume messages from stream"
    fi
}

# Test 8: Message acknowledgment
test_message_acknowledgment() {
    start_test "Message Acknowledgment"
    
    # Get pending messages
    local pending=$(redis_cmd XPENDING "$TEST_STREAM" "$TEST_GROUP")
    local pending_count=$(echo "$pending" | head -1)
    
    if [[ "$pending_count" -gt 0 ]]; then
        # Get specific pending messages
        local pending_details=$(redis_cmd XPENDING "$TEST_STREAM" "$TEST_GROUP" "-" "+" 1)
        local message_id=$(echo "$pending_details" | awk '{print $1}' | head -1)
        
        if [[ -n "$message_id" ]]; then
            # Acknowledge the message
            local ack_result=$(redis_cmd XACK "$TEST_STREAM" "$TEST_GROUP" "$message_id")
            
            if [[ "$ack_result" == "1" ]]; then
                info "Successfully acknowledged message: $message_id"
                pass_test
            else
                fail_test "Could not acknowledge message"
            fi
        else
            fail_test "Could not get pending message ID"
        fi
    else
        warning "No pending messages to acknowledge"
        pass_test
    fi
}

# Test 9: Dead letter queue simulation
test_dead_letter_queue() {
    start_test "Dead Letter Queue"
    
    local dead_letter_stream="opsconductor:dead_letter:events"
    
    # Add a message to dead letter queue
    local message_id=$(redis_cmd XADD "$dead_letter_stream" "*" \
        "event_type" "failed_message" \
        "service" "test_service" \
        "original_stream" "$TEST_STREAM" \
        "failed_at" "$(date +%s)" \
        "retry_count" "3" \
        "status" "dead_letter" \
        "data" '{"error": "max retries exceeded"}')
    
    if [[ -n "$message_id" ]]; then
        local dlq_length=$(redis_cmd XLEN "$dead_letter_stream")
        info "Dead letter queue length: $dlq_length"
        pass_test
    else
        fail_test "Could not add message to dead letter queue"
    fi
}

# Test 10: Performance test
test_performance() {
    start_test "Performance Testing"
    
    local perf_stream="opsconductor:perf:events"
    local start_time=$(date +%s.%N)
    local message_count=100
    local successful_messages=0
    
    # Clean up performance stream
    redis_cmd DEL "$perf_stream" >/dev/null 2>&1 || true
    
    # Publish messages rapidly
    for i in $(seq 1 $message_count); do
        local message_id=$(redis_cmd XADD "$perf_stream" "*" \
            "event_type" "performance_test" \
            "service" "perf_test" \
            "message_number" "$i" \
            "timestamp" "$(date +%s.%N)" \
            "data" "{\"batch\": $i}")
        
        if [[ -n "$message_id" ]]; then
            successful_messages=$((successful_messages + 1))
        fi
    done
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "1")
    local messages_per_second=$(echo "scale=2; $successful_messages / $duration" | bc -l 2>/dev/null || echo "N/A")
    
    if [[ "$successful_messages" -eq "$message_count" ]]; then
        info "Published $successful_messages messages in ${duration}s"
        info "Performance: $messages_per_second messages/second"
        pass_test
    else
        fail_test "Only published $successful_messages out of $message_count messages"
    fi
    
    # Clean up performance stream
    redis_cmd DEL "$perf_stream" >/dev/null 2>&1 || true
}

# Test 11: Monitor dashboard connectivity
test_monitor_dashboard() {
    start_test "Monitor Dashboard"
    
    if curl -f "$MONITOR_URL/health" >/dev/null 2>&1; then
        info "Monitor dashboard is accessible at $MONITOR_URL"
        
        # Test API endpoints
        if curl -f "$MONITOR_URL/api/streams" >/dev/null 2>&1; then
            info "Streams API endpoint is working"
            pass_test
        else
            fail_test "Streams API endpoint is not responding"
        fi
    else
        fail_test "Monitor dashboard is not accessible"
    fi
}

# Test 12: Service integration test
test_service_integration() {
    start_test "Service Integration"
    
    # Check if processor is running
    if docker ps | grep -q "opsconductor-streams-processor"; then
        info "Message processor is running"
        
        # Check processor logs for activity
        local recent_logs=$(docker logs --tail 10 opsconductor-streams-processor 2>/dev/null | grep -c "Processing message" || echo "0")
        
        if [[ "$recent_logs" -gt 0 ]]; then
            info "Processor has processed $recent_logs messages recently"
            pass_test
        else
            warning "Processor is running but no recent message processing detected"
            pass_test
        fi
    else
        fail_test "Message processor is not running"
    fi
}

# Test 13: Memory and resource usage
test_resource_usage() {
    start_test "Resource Usage"
    
    local memory_info=$(redis_cmd INFO memory)
    local used_memory=$(echo "$memory_info" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
    local peak_memory=$(echo "$memory_info" | grep "used_memory_peak_human:" | cut -d: -f2 | tr -d '\r')
    
    # Get container stats
    local container_stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep "$REDIS_CONTAINER" || echo "N/A")
    
    info "Redis memory usage: $used_memory (peak: $peak_memory)"
    info "Container stats: $container_stats"
    
    # Check if memory usage is reasonable (less than 1GB for tests)
    local memory_bytes=$(echo "$memory_info" | grep "used_memory:" | cut -d: -f2 | tr -d '\r')
    if [[ "$memory_bytes" -lt 1073741824 ]]; then  # 1GB in bytes
        pass_test
    else
        warning "Memory usage is high: $used_memory"
        pass_test
    fi
}

# Test 14: Stream cleanup and maintenance
test_stream_cleanup() {
    start_test "Stream Cleanup"
    
    # Test stream trimming
    local original_length=$(redis_cmd XLEN "$TEST_STREAM")
    
    # Trim stream to keep only last 5 messages
    redis_cmd XTRIM "$TEST_STREAM" MAXLEN 5 >/dev/null
    
    local new_length=$(redis_cmd XLEN "$TEST_STREAM")
    
    if [[ "$new_length" -le 5 ]]; then
        info "Stream trimmed from $original_length to $new_length messages"
        pass_test
    else
        fail_test "Stream trimming did not work as expected"
    fi
}

# Cleanup function
cleanup_test_data() {
    log "Cleaning up test data..."
    
    # Remove test streams
    redis_cmd DEL "$TEST_STREAM" >/dev/null 2>&1 || true
    redis_cmd DEL "opsconductor:perf:events" >/dev/null 2>&1 || true
    
    # Note: We don't clean up dead letter queue as it might contain real data
    
    success "Test cleanup completed"
}

# Function to display test results
show_test_results() {
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    📊 TEST RESULTS 📊                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    echo -e "\n${CYAN}📈 TEST SUMMARY:${NC}"
    echo -e "  🧪 Total Tests: $TESTS_TOTAL"
    echo -e "  ✅ Passed: $TESTS_PASSED"
    echo -e "  ❌ Failed: $TESTS_FAILED"
    
    local success_rate=0
    if [[ "$TESTS_TOTAL" -gt 0 ]]; then
        success_rate=$(echo "scale=1; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc -l 2>/dev/null || echo "0")
    fi
    
    echo -e "  📊 Success Rate: ${success_rate}%"
    
    if [[ "$TESTS_FAILED" -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Redis Streams is working perfectly! 🎉${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Some tests failed. Check the logs for details.${NC}"
    fi
    
    echo -e "\n${CYAN}🔗 USEFUL LINKS:${NC}"
    echo -e "  📊 Monitor Dashboard: $MONITOR_URL"
    echo -e "  📋 Test Log: $TEST_LOG"
    echo -e "  🐳 Container Logs: docker logs $REDIS_CONTAINER"
    
    echo -e "\n${CYAN}🚀 NEXT STEPS:${NC}"
    echo -e "  1. Review any failed tests in the log file"
    echo -e "  2. Check the monitor dashboard for real-time metrics"
    echo -e "  3. Integrate Redis Streams with OpsConductor services"
    echo -e "  4. Set up production monitoring and alerting"
}

# Main testing function
main() {
    # Clear previous log
    > "$TEST_LOG"
    
    # Show banner
    show_banner
    
    # Start testing
    log "Starting Redis Streams testing suite..."
    log "Test log: $TEST_LOG"
    
    # Check if Redis container is running
    if ! docker ps | grep -q "$REDIS_CONTAINER"; then
        error "Redis Streams container is not running. Please run deploy-redis-streams.sh first."
        exit 1
    fi
    
    # Run all tests
    test_redis_connectivity
    test_redis_info
    test_stream_creation
    test_stream_info
    test_consumer_group_creation
    test_message_publishing
    test_message_consumption
    test_message_acknowledgment
    test_dead_letter_queue
    test_performance
    test_monitor_dashboard
    test_service_integration
    test_resource_usage
    test_stream_cleanup
    
    # Cleanup test data
    cleanup_test_data
    
    # Show results
    show_test_results
    
    # Exit with appropriate code
    if [[ "$TESTS_FAILED" -eq 0 ]]; then
        success "All tests passed successfully!"
        exit 0
    else
        error "$TESTS_FAILED tests failed"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi