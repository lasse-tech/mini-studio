REQUIRED := clean distclean debug install uninstall deploy lint
HELP_VARS := PREFIX

.DEFAULT_GOAL := help

PYTHON := python3 -W error
APP_FILES := app.py calliope_backend.py main.ts pxt.json mkc.json

##@ Build

## PREFIX: install root for the editor
PREFIX ?= $(HOME)/.local

SHARE := $(PREFIX)/share/mini-studio
BIN := $(PREFIX)/bin/mini-studio

## help: list targets and variables
help:
	@$(foreach v,$(HELP_VARS),$(v)='$($(v))') awk -f scripts/make-help.awk $(firstword $(MAKEFILE_LIST))

## build: compile main.ts to built/v3/binary.hex
build:
	mkc build

## flash: build and copy the HEX to a mounted Calliope mini V3
flash: build
	$(PYTHON) -c 'from pathlib import Path; import calliope_backend as c; print(c.flash(Path("built/v3/binary.hex")))'

## debug: start the editor from the working tree, warnings as errors
debug:
	$(PYTHON) -X dev app.py

## install: install the editor and the example to PREFIX
install:
	install -d $(SHARE) $(PREFIX)/bin
	install -m 644 $(APP_FILES) $(SHARE)
	chmod 755 $(SHARE)/app.py
	ln -sf $(SHARE)/app.py $(BIN)

## uninstall: remove what install put in place
uninstall:
	rm -f $(BIN)
	rm -rf $(SHARE)

## deploy: nothing to deploy, no web server
deploy:
	@echo "Nothing to deploy: Mini Studio is a desktop app without a web server."

##@ Maintenance

## lint: ruff, ruff format, MakeCode type check, Makefile comment rules
lint:
	ruff check .
	ruff format --check .
	mkc build
	@awk -v required="$(REQUIRED)" -f scripts/make-lint.awk $(firstword $(MAKEFILE_LIST))

## clean: remove build output
clean:
	rm -rf built __pycache__

## distclean: clean plus the MakeCode caches
distclean: clean
	rm -rf .pxt node_modules

.PHONY: help build flash debug install uninstall deploy lint clean distclean
