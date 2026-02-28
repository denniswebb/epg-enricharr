.PHONY: help test-zip validate setup-dispatcharr install-plugin check-output clean

VERSION := 1.0.0
PLUGIN_NAME := epg-enricharr
ZIP_FILE := $(PLUGIN_NAME)-$(VERSION).zip
PLUGIN_DIR := ./plugin
BUILD_DIR := ./build
DISPATCHARR_PLUGIN_DIR ?= ~/.dispatcharr/plugins

help:
	@echo "epg-enricharr Local Development Targets"
	@echo "========================================"
	@echo ""
	@echo "setup:"
	@echo "  make setup-dispatcharr     Set up local Dispatcharr instance (Docker)"
	@echo "  make dev-setup             Install development dependencies"
	@echo ""
	@echo "building:"
	@echo "  make test-zip              Generate plugin zip package"
	@echo "  make clean                 Remove build artifacts"
	@echo ""
	@echo "testing:"
	@echo "  make validate              Validate plugin zip structure and tests"
	@echo "  make install-plugin        Install plugin to local Dispatcharr"
	@echo "  make check-output          Verify enrichment output on test EPG data"
	@echo ""
	@echo "usage:"
	@echo "  make help                  Show this help message"

# Development environment setup
dev-setup:
	@echo "Installing development dependencies..."
	./dev-setup.sh
	@echo "✅ Development environment ready"

# Generate plugin zip
test-zip: clean
	@echo "Building plugin zip..."
	@mkdir -p $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)
	@cp plugin.json $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/
	@cp plugin.py $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/
	@cp README.md $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/
	@cp LICENSE $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/ 2>/dev/null || echo "No LICENSE file"
	@mkdir -p $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/tests
	@cp tests/test_enrichment.py $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/tests/ 2>/dev/null || echo "No test file"
	@mkdir -p $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/tests/fixtures
	@cp tests/fixtures/*.xml $(BUILD_DIR)/$(PLUGIN_NAME)-$(VERSION)/tests/fixtures/ 2>/dev/null || echo "No fixture files"
	@cd $(BUILD_DIR) && zip -r ../$(ZIP_FILE) $(PLUGIN_NAME)-$(VERSION) > /dev/null
	@echo "✅ Plugin zip created: $(ZIP_FILE)"

# Validate plugin
validate:
	@echo "Validating plugin..."
	@python3 validation.py $(ZIP_FILE)

# Set up local Dispatcharr (Docker)
setup-dispatcharr:
	@echo "Setting up local Dispatcharr instance..."
	@if command -v docker &> /dev/null; then \
		docker run -d --name dispatcharr-dev \
			-p 8000:8000 \
			-v $$(pwd)/tests/fixtures:/app/data/fixtures \
			-e DEBUG=True \
			--rm \
			python:3.11 \
			bash -c "pip install django && python -m django startproject dispatcharr /app && python /app/manage.py runserver 0.0.0.0:8000" \
			2>/dev/null || docker start dispatcharr-dev; \
		echo "✅ Dispatcharr available at http://localhost:8000"; \
	else \
		echo "⚠️  Docker not found. Use dev-setup.sh to set up Python environment instead."; \
		echo "See docs/SETUP.md for native installation steps."; \
	fi

# Install plugin to local instance
install-plugin: test-zip
	@echo "Installing plugin to local Dispatcharr..."
	@if [ -d "$(DISPATCHARR_PLUGIN_DIR)" ]; then \
		mkdir -p $(DISPATCHARR_PLUGIN_DIR); \
		unzip -q -o $(ZIP_FILE) -d $(DISPATCHARR_PLUGIN_DIR); \
		echo "✅ Plugin installed to $(DISPATCHARR_PLUGIN_DIR)"; \
	else \
		echo "⚠️  Dispatcharr plugin directory not found: $(DISPATCHARR_PLUGIN_DIR)"; \
		echo "Set DISPATCHARR_PLUGIN_DIR or ensure Dispatcharr is installed."; \
		exit 1; \
	fi

# Validate enriched output
check-output:
	@echo "Checking enrichment output..."
	@if [ -f tests/fixtures/sample-epg.xml ]; then \
		python3 scripts/validate_output.py tests/fixtures/sample-epg.xml; \
	else \
		echo "⚠️  No test EPG data found. Run 'make test-zip' first."; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR) $(ZIP_FILE)
	@echo "✅ Clean complete"
