# Poker Lern-Assistent - Erste Implementierungsphase

Die Anwendung erfasst ausschließlich Fensterinhalte und führt keine Eingaben,
Klicks oder Pokeraktionen aus. Der aktuelle Stand implementiert Fensteraufnahme
und Template-Erkennung; Pokerberechnung und Qt-Overlay sind noch nicht enthalten.

## Installation

```powershell
uv sync
uv run python tools\generate_demo_templates.py
```

## Start

```powershell
uv run python main.py --window GGPoker --layout ggpoker_default --timings
```

Ohne eindeutigen Titel wird eine numerische Fensterauswahl angezeigt.

## Reale Kartenvorlagen

Die Demo-Vorlagen werden mit
`uv run python tools\generate_demo_templates.py` erzeugt. Für echte Erkennung
müssen alle 52 PNG-Dateien `As.png`, `Ah.png`, `Ad.png`, `Ac.png`, ... als reale,
kalibrierte Ausschnitte aus der verwendeten Pokeroberfläche erstellt werden.
Die Regiongrößen in `config.py` müssen an die tatsächliche Fensterauflösung
angepasst werden.

## Layoutkalibrierung

`LayoutConfig` speichert alle Kartenpositionen relativ zur Fenstergröße. Bei
Fenstergrößenänderungen werden die Positionen automatisch neu berechnet.
Mehrere Tischlayouts können als weitere benannte `LayoutConfig`-Einträge
in `AppConfig.layouts` ergänzt werden.

## Entwicklung und Tests

```powershell
uv run pytest --cov
uv run ruff check .
uv run python -m mypy .
```

`eval7` stellt auf Windows keine installierbare Distribution bereit und ist
deshalb in `pyproject.toml` auf Linux x86_64 beschränkt. Es wird vom aktuellen
Code noch nicht importiert.

Siehe [AUDIT.md](./AUDIT.md) für den technischen Audit, die nachgewiesenen
Grenzen und die bislang nicht verifizierbaren Performance-/Bildqualitätsfragen.
