# OpsConductor Development Makefile

.PHONY: help setup-dev validate-volumes update-volumes install-hooks check-mounts

help: ## Show this help message
	@echo "OpsConductor Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Volume Mount Management:"
	@echo "  make validate-volumes    - Check all volume mounts are selective"
	@echo "  make update-volumes SVC=<service> - Generate mounts for service"
	@echo "  make install-hooks       - Install pre-commit validation hook"
	@echo ""

setup-dev: install-hooks ## Set up development environment
	@echo "🔧 Setting up development environment..."
	@chmod +x scripts/*.sh
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Run 'make validate-volumes' to check current setup"
	@echo "2. Use 'make update-volumes SVC=service-name' when adding new files"

validate-volumes: ## Validate all volume mounts are selective
	@echo "🔍 Validating volume mounts..."
	@./scripts/check-volume-mounts.sh

update-volumes: ## Generate selective volume mounts for a service (use: make update-volumes SVC=service-name)
	@if [ -z "$(SVC)" ]; then \
		echo "❌ Error: Please specify service name"; \
		echo "Usage: make update-volumes SVC=ai-service"; \
		exit 1; \
	fi
	@echo "🔧 Generating volume mounts for $(SVC)..."
	@./scripts/update-volume-mounts.sh $(SVC)

update-zenrule: ## Auto-update ZenRule with current docker-compose.yml configurations
	@echo "🔄 Updating ZenRule with current configurations..."
	@./scripts/auto-update-zenrule.sh

install-hooks: ## Install pre-commit hooks for volume mount validation
	@echo "🔧 Installing pre-commit hooks..."
	@chmod +x scripts/pre-commit-hook.sh
	@cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hooks installed!"

check-mounts: validate-volumes ## Alias for validate-volumes

# Docker commands with volume mount safety
docker-build: validate-volumes ## Build all services (validates mounts first)
	@echo "🔍 Volume mounts validated - proceeding with build..."
	docker compose build

docker-up: validate-volumes ## Start all services (validates mounts first)  
	@echo "🔍 Volume mounts validated - starting services..."
	docker compose up -d

docker-restart: validate-volumes ## Restart all services (validates mounts first)
	@echo "🔍 Volume mounts validated - restarting services..."
	docker compose restart

# Service-specific commands
restart-service: ## Restart a specific service (use: make restart-service SVC=service-name)
	@if [ -z "$(SVC)" ]; then \
		echo "❌ Error: Please specify service name"; \
		echo "Usage: make restart-service SVC=ai-service"; \
		exit 1; \
	fi
	@make validate-volumes
	@echo "🔄 Restarting $(SVC)..."
	@docker compose restart $(SVC)

logs-service: ## Show logs for a specific service (use: make logs-service SVC=service-name)
	@if [ -z "$(SVC)" ]; then \
		echo "❌ Error: Please specify service name"; \
		echo "Usage: make logs-service SVC=ai-service"; \
		exit 1; \
	fi
	@docker compose logs -f $(SVC)

# Emergency commands
fix-all-mounts: ## Emergency: Fix all volume mounts to be selective
	@echo "🚨 EMERGENCY: Converting all volume mounts to selective..."
	@echo "This will update docker-compose.yml with selective mounts for all services"
	@read -p "Are you sure? This will modify docker-compose.yml [y/N]: " confirm && [ "$$confirm" = "y" ]
	@for service in api-gateway identity-service asset-service automation-service communication-service ai-service; do \
		if [ -d "./$$service" ]; then \
			echo "Generating mounts for $$service..."; \
			./scripts/update-volume-mounts.sh $$service; \
		fi; \
	done
	@echo ""
	@echo "⚠️  MANUAL STEP REQUIRED:"
	@echo "1. Copy the generated mount configurations to docker-compose.yml"
	@echo "2. Update .zenrules/selective-volume-mounts.md"
	@echo "3. Run 'make validate-volumes' to verify"

# Documentation
show-zenrule: ## Show the volume mount ZenRule
	@cat .zenrules/selective-volume-mounts.md

# Quick status check
status: ## Show system status and validate mounts
	@echo "🔍 OpsConductor System Status"
	@echo "=============================="
	@echo ""
	@echo "📋 Docker Services:"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not running or no services"
	@echo ""
	@echo "🔍 Volume Mount Validation:"
	@./scripts/check-volume-mounts.sh
	@echo ""
	@echo "✅ System status check complete!"