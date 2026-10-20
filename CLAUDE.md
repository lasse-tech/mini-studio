# Mini Studio

GTK-Editor und Flasher für MakeCode-TypeScript auf dem Calliope mini V3. Beispiel in `main.ts`: Hauptthema des Imperial March.

- Zugehörigkeit: **lars-gossard.de** (privates Projekt), Copyright `2026 Lars Gossard`, Lizenz MIT.
- Remotes: `origin` auf Forgejo (`gossardla/mini-studio`), `github` (`lasse-tech/mini-studio`, öffentlich) als Backup.
- Öffentliches Projekt: kein Installations- oder Deploy-Skript für Server.
- Einstieg nur über Make: `make debug`, `make build`, `make flash`, `make lint`.
- `basic.showLeds` pausiert ohne zweites Argument 400 ms — im Takt immer `showLeds(…, 0)`.
- Melodie aus `midi/imperial-march.mid`, Trompetenspur Takt 6–17, auf 16tel quantisiert.

## Offen

- Oberfläche ist nur deutsch: muss Englisch werden, Deutsch als Zweitsprache.
- About-Dialog fehlt (Copyright, Lizenz, Chip `Made with <3 in Europe`).
