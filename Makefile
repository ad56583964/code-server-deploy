SHELL := /usr/bin/env bash

# Ubuntu 24.04 code-server deployment helper

CODE_SERVER_VERSION ?= 4.102.3
CODE_SERVER_DEB_URL ?= https://github.com/coder/code-server/releases/download/v$(CODE_SERVER_VERSION)/code-server_$(CODE_SERVER_VERSION)_amd64.deb

CODE_SERVER_USER ?= $(USER)
# Must be provided explicitly when running `make setup-systemd` or `make deploy`.
CODE_SERVER_PASSWORD ?=

.PHONY: help install-deps install-code-server install-cert setup-systemd deploy

help:
	@echo "Targets:"
	@echo "  install-deps            Install system dependencies (python3, openssl, curl, wget, make, git)"
	@echo "  install-code-server     Install code-server $(CODE_SERVER_VERSION) on Ubuntu 24.04"
	@echo "  install-cert            Generate self-signed TLS cert and place it into code-server config dir"
	@echo "  setup-systemd           Configure systemd service code-server@<user>"
	@echo "  deploy                  install-deps + install-code-server + install-cert + setup-systemd"
	@echo ""
	@echo "Examples:"
	@echo "  make install-deps"
	@echo "  make install-code-server"
	@echo "  make install-cert HOST=my.code-server.local"
	@echo "  make setup-systemd CODE_SERVER_PASSWORD=your-strong-password"
	@echo "  make deploy HOST=my.domain CODE_SERVER_PASSWORD=your-strong-password"

install-deps:
	sudo apt update
	sudo apt install -y python3 python3-venv python3-pip openssl curl wget make git

install-code-server:
	cd /tmp && wget -O code-server_$(CODE_SERVER_VERSION)_amd64.deb "$(CODE_SERVER_DEB_URL)"
	cd /tmp && sudo dpkg -i code-server_$(CODE_SERVER_VERSION)_amd64.deb || sudo apt -f install -y
	code-server --version

install-cert:
	python3 scripts/gen_self_signed_cert.py $(if $(HOST),--host "$(HOST)",) $(if $(OUT_DIR),--out-dir "$(OUT_DIR)",)

setup-systemd:
	@if [ -z "$(CODE_SERVER_PASSWORD)" ]; then \
		echo "ERROR: CODE_SERVER_PASSWORD is empty."; \
		echo "Usage: make setup-systemd CODE_SERVER_PASSWORD=your-strong-password"; \
		exit 1; \
	fi
	sudo mkdir -p /etc/systemd/system/code-server@.service.d
	printf "[Service]\nEnvironment=PASSWORD=%s\n" "$(CODE_SERVER_PASSWORD)" | sudo tee /etc/systemd/system/code-server@.service.d/override.conf >/dev/null
	sudo systemctl daemon-reload
	sudo systemctl enable --now "code-server@$(CODE_SERVER_USER)"
	systemctl status "code-server@$(CODE_SERVER_USER)" --no-pager || true

deploy: install-deps install-code-server install-cert setup-systemd
