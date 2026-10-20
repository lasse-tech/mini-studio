REQUIRED := clean distclean debug install uninstall deploy lint
HELP_VARS := PREFIX

.DEFAULT_GOAL := help

PYTHON := python3 -W error
APP_FILES := app.py calliope_backend.py i18n.py matrix.py mini-studio.css main.ts pxt.json mkc.json
SOURCES := app.py calliope_backend.py matrix.py
LANGUAGES := de
MO := $(foreach l,$(LANGUAGES),locale/$(l)/LC_MESSAGES/mini-studio.mo)
XGETTEXT := xgettext --language=Python --keyword=_ --from-code=UTF-8 --package-name=mini-studio

##@ Build

## PREFIX: install root for the editor
PREFIX ?= $(HOME)/.local

SHARE := $(PREFIX)/share/mini-studio
BIN := $(PREFIX)/bin/mini-studio
DESKTOP := $(PREFIX)/share/applications/mini-studio.desktop
ICON := $(PREFIX)/share/icons/hicolor/scalable/apps/mini-studio.svg

## help: list targets and variables
help:
	@$(foreach v,$(HELP_VARS),$(v)='$($(v))') awk -f scripts/make-help.awk $(firstword $(MAKEFILE_LIST))

## build: compile main.ts to built/v3/binary.hex
build:
	mkc build

## locale: compile the translations in po/ to locale/
locale: $(MO)

locale/%/LC_MESSAGES/mini-studio.mo: po/%.po
	mkdir -p $(dir $@)
	msgfmt --check -o $@ $<

## pot: extract strings to po/mini-studio.pot and merge them into every po file
pot:
	$(XGETTEXT) --add-comments --sort-by-file -o po/mini-studio.pot $(SOURCES)
	$(foreach l,$(LANGUAGES),msgmerge --quiet --update --backup=none po/$(l).po po/mini-studio.pot;)

## flash: build and copy the HEX to a mounted Calliope mini V3
flash: build
	$(PYTHON) -c 'from pathlib import Path; import calliope_backend as c; print(c.flash(Path("built/v3/binary.hex")))'

## debug: start the editor from the working tree, warnings as errors
debug: locale
	$(PYTHON) -X dev app.py

## install: install the editor and the example to PREFIX
install: locale
	install -d $(SHARE) $(PREFIX)/bin
	install -m 644 $(APP_FILES) $(SHARE)
	cp -r locale $(SHARE)
	chmod 755 $(SHARE)/app.py
	ln -sf $(SHARE)/app.py $(BIN)
	install -d $(dir $(DESKTOP)) $(dir $(ICON))
	sed 's|^Exec=.*|Exec=$(BIN)|' mini-studio.desktop > $(DESKTOP)
	install -m 644 mini-studio.svg $(ICON)

## uninstall: remove what install put in place
uninstall:
	rm -f $(BIN) $(DESKTOP) $(ICON)
	rm -rf $(SHARE)

## deploy: nothing to deploy, no web server
deploy:
	@echo "Nothing to deploy: Mini Studio is a desktop app without a web server."

##@ Maintenance

## lint: ruff, ruff format, translations complete, MakeCode type check, Makefile comments
lint:
	ruff check .
	ruff format --check .
	$(foreach l,$(LANGUAGES),$(XGETTEXT) -o - $(SOURCES) | msgcmp po/$(l).po - &&) true
	$(foreach l,$(LANGUAGES),msgfmt --check -o /dev/null po/$(l).po &&) true
	mkc build
	@awk -v required="$(REQUIRED)" -f scripts/make-lint.awk $(firstword $(MAKEFILE_LIST))

## clean: remove build output
clean:
	rm -rf built __pycache__ locale

## distclean: clean plus the MakeCode caches
distclean: clean
	rm -rf .pxt node_modules

.PHONY: help build locale pot flash debug install uninstall deploy lint clean distclean
