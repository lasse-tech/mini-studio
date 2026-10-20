REQUIRED := clean distclean debug install uninstall deploy lint
HELP_VARS := PREFIX EXAMPLE

.DEFAULT_GOAL := help

PYTHON := python3 -W error
APP_FILES := app.py calliope_backend.py i18n.py library.py matrix.py mini-studio.css
SOURCES := app.py calliope_backend.py library.py matrix.py
PROJECTS := $(notdir $(wildcard library/*))
PRIVATE := CLAUDE.md
LANGUAGES := de
MO := $(foreach l,$(LANGUAGES),locale/$(l)/LC_MESSAGES/mini-studio.mo)
XGETTEXT := xgettext --language=Python --keyword=_ --from-code=UTF-8 --package-name=mini-studio

##@ Build

## PREFIX: install root for the editor
PREFIX ?= $(HOME)/.local

## EXAMPLE: library project that build and flash use
EXAMPLE ?= imperial-march

SHARE := $(PREFIX)/share/mini-studio
BIN := $(PREFIX)/bin/mini-studio
DESKTOP := $(PREFIX)/share/applications/mini-studio.desktop
ICON_THEME := $(PREFIX)/share/icons/hicolor
ICON := $(ICON_THEME)/scalable/apps/mini-studio.svg
REFRESH_MENU := gtk-update-icon-cache --quiet --force --ignore-theme-index $(ICON_THEME); update-desktop-database --quiet $(dir $(DESKTOP))

## help: list targets and variables
help:
	@$(foreach v,$(HELP_VARS),$(v)='$($(v))') awk -f scripts/make-help.awk $(firstword $(MAKEFILE_LIST))

## build: compile library/EXAMPLE to its built/v3/binary.hex
build:
	cd library/$(EXAMPLE) && mkc build

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
	$(PYTHON) -c 'from pathlib import Path; import calliope_backend as c; print(c.flash(Path("library/$(EXAMPLE)/built/v3/binary.hex")))'

## debug: start the editor from the working tree, warnings as errors
debug: locale
	$(PYTHON) -X dev app.py

## install: install the editor and the example to PREFIX
install: locale
	install -d $(SHARE) $(PREFIX)/bin
	install -m 644 $(APP_FILES) $(SHARE)
	cp -r locale $(SHARE)
	rm -rf $(SHARE)/library
	tar -c --exclude=built --exclude=.pxt library | tar -x -C $(SHARE)
	chmod 755 $(SHARE)/app.py
	ln -sf $(SHARE)/app.py $(BIN)
	install -d $(dir $(DESKTOP)) $(dir $(ICON))
	sed 's|^Exec=.*|Exec=$(BIN)|' mini-studio.desktop > $(DESKTOP)
	install -m 644 mini-studio.svg $(ICON)
	$(REFRESH_MENU)

## uninstall: remove what install put in place
uninstall:
	rm -f $(BIN) $(DESKTOP) $(ICON)
	$(REFRESH_MENU)
	rm -rf $(SHARE)

## screenshot: docs/screenshot.png for the README, English, fresh library copy
screenshot: locale
	rm -rf .screenshot-home && mkdir -p .screenshot-home docs
	HOME=$(CURDIR)/.screenshot-home LANGUAGE=en LANG=en_US.UTF-8 PYTHONPATH=$(CURDIR) xvfb-run -a -s "-screen 0 1280x800x24" $(PYTHON) scripts/screenshot.py docs/screenshot.png
	rm -rf .screenshot-home

## github: push main to GitHub, with history rewritten without CLAUDE.md
github:
	git push github $$($(PYTHON) -I scripts/github_export.py main $(PRIVATE)):refs/heads/main

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
	$(foreach p,$(PROJECTS),(cd library/$(p) && mkc build) &&) true
	@awk -v required="$(REQUIRED)" -f scripts/make-lint.awk $(firstword $(MAKEFILE_LIST))

## clean: remove build output
clean:
	rm -rf __pycache__ locale library/*/built

## distclean: clean plus the MakeCode caches
distclean: clean
	rm -rf library/*/.pxt library/*/node_modules

.PHONY: help build locale pot flash github screenshot debug install uninstall deploy lint clean distclean
