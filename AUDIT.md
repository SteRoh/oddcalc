# Technischer Audit: Poker-Lernprojekt

## Umfang und Aussagekraft

Die Datei-Bewertungen beschreiben den vor den Korrekturen untersuchten
Ausgangsstand. Umgesetzte Änderungen und die Verifikation im aktuellen
Workspace sind am Ende des Berichts separat festgehalten.

Der Workspace enthält `main.py`, `config.py`, drei Module unter `vision/`,
zwei `unittest`-Dateien, einen Demo-Template-Generator und `requirements.txt`.
Es gibt weder einen Pokerlogik-/Odds-Baustein noch ein Qt-Fenster/Overlay,
eine CI-Konfiguration, echte Kartenvorlagen oder Screenshot-Testdaten. Aussagen
zu diesen nicht vorhandenen Komponenten sind daher eine Bestandslücke, keine
Bewertung einer Implementierung.

Die Tests konnten vor der Projektkonfiguration nicht mit `uv run pytest`
gestartet werden (`pytest` nicht gefunden). Die Pylance-Importanalyse löste
`cv2`, `numpy` und `mss` auf, fand aber keine unaufgelösten Importe. Die lokale
Pylance-Laufzeit konnte `cv2` wegen einer Windows-Anwendungssteuerungsrichtlinie
nicht laden; ein Laufzeit-/Bildqualitätsurteil ist damit vorerst nicht möglich.
Die Laufzeitumgebung stellt Python 3.14.3 bereit; Python 3.12 wurde hier nicht
verifiziert.

## Architektur und Wartbarkeit

- **Struktur/Trennung:** `config.py` enthält relative Kartenregionen;
  `vision/capture.py` kapselt Win32-Fensterauflistung und MSS-Aufnahme;
  `vision/template_matcher.py` lädt/matcht PNGs; `vision/card_detector.py`
  verbindet Layout und Matcher; `main.py` ist CLI und Ablaufsteuerung. Die
  Trennung ist für einen kleinen Prototyp verständlich, aber Konfiguration,
  Erkennung und UI sind noch nicht als austauschbare Schnittstellen modelliert.
- **Abhängigkeiten:** CV-Code importiert OpenCV/NumPy; Aufnahme nutzt MSS;
  `main.py` nutzt die Komponenten. `PyQt6` und `eval7` stehen in
  `requirements.txt`, werden im vorhandenen Python-Code jedoch nicht verwendet.
  Es gibt keine Paket-/uv-Projektdefinition.
- **Kopplung/Testbarkeit:** Der Matcher ist isoliert testbar; die Capture-Klasse
  bindet die Windows-API direkt und ist ohne Mock schwer zu testen. Eine Qt-UI
  oder Pokerlogik existiert nicht.
- **Wartbarkeit/Erweiterbarkeit/Testbarkeit:** angemessen für den Prototyp,
  schwach für einen vollständigen Lernassistenten. Layouts lassen sich ergänzen,
  aber Variabilität von DPI, Skalierung und Tisch-UI wird nicht kalibriert.
  Testbarkeit wird durch das Fehlen von Abhängigkeitsinjektion, Testdaten und
  Projekt-Testkonfiguration begrenzt.
- **Zirkuläre Importe/God Classes/lange Methoden:** in der vorliegenden
  überschaubaren Struktur nicht erkennbar. Keine Methode ist auffällig lang.
  `main()` übernimmt Auswahl, Aufnahme, Erkennung, Ausgabe und Fehlerinteraktion,
  bleibt aber derzeit klein genug, um keine God Class/Long Method zu sein.

## Datei-für-Datei-Befund

| Datei | Befund |
|---|---|
| `main.py` | CLI-Ablauf; ungenutzter Import `LayoutConfig`; `choose_window` ist unpräzise als `object` typisiert. Die Schleife hat keine Taktbegrenzung und verarbeitet eine unveränderte Fenstergeometrie weiter. Fehler enden in einer blockierenden `input()`-Abfrage. |
| `config.py` | Datenklassen sind klar; Regionwerte werden nicht auf gültige endliche Bruchteile validiert. `Dict` kann als modernes `dict` typisiert werden. |
| `vision/capture.py` | Win32-API-Funktionssignaturen sind nicht festgelegt; ctypes-Standard-Rückgabetypen können Handles auf 64-Bit-Windows abschneiden. MSS-Kontext wird für jede Aufnahme neu erstellt. Fensterkoordinaten/-größe werden nach Auswahl nicht aktualisiert; DPI-Awareness ist nicht gesetzt. Import `Iterable` und Callback-Parameter `_lparam` bleiben ungenutzt. |
| `vision/card_detector.py` | Import `cv2` ungenutzt; `region: object` verliert Typinformation. Es gibt keine Validierung der Screenshot-Form und keine Duplikat-/Kartenanzahlprüfung. Nicht erkannte Positionen werden aus Ergebnislisten entfernt, wodurch Slots nicht mehr eindeutig abgebildet sind. |
| `vision/template_matcher.py` | Keine Validierung von Threshold, Bildformat oder Kartenkennung; ungültige PNGs werden ignoriert. Keine Skalierung/Normalisierung für DPI- oder Größenabweichungen. `TM_CCOEFF_NORMED` ist bei flachen/konstanten Bildern degeneriert und kann hohe Scores liefern; die bestehenden konstanten Testbilder belegen deshalb keine Erkennungsqualität. Score ist ein Korrelationswert, keine Match-Wahrscheinlichkeit. |
| `vision/__init__.py` | Leer, aber als Paketmarker legitim; keine unnötige Funktionalität. |
| `tests/test_template_matcher.py` | `unittest` statt pytest-Stil, aber grundsätzlich pytest-kompatibel. Die zwei Tests benutzen konstante Bildflächen und können False Positives nicht erkennen; keine Größen-, Invalid-Input-, Mehrkarten- oder realen Bildtests. |
| `tests/test_card_detector.py` | Test nutzt für alle Karten dasselbe einfarbige Bild und erwartet dadurch fünfmal dieselbe Karte; prüft nur das Durchreichen von Regionen, keine Kartenerkennung. |
| `tools/generate_demo_templates.py` | Erzeugt synthetische, nicht repräsentative Vorlagen. Rückgabewerte von `cv2.imwrite` werden nicht geprüft. Die Datei weist zutreffend auf den Demo-Charakter hin. |
| `README.md` | Dokumentiert Demo-Vorlagen und Layoutanpassung. Installationsanleitung verwendet `venv`/`pip`, obwohl die geforderte Verwaltung `uv` ist. Kein Hinweis auf fehlende GUI-/Pokerlogik. |
| `requirements.txt` | Laufzeitpakete sind nur grob versioniert; `PyQt6` und `eval7` sind aktuell ungenutzt. Test-, Lint- und Typprüfungswerkzeuge fehlen. |

## Computer Vision und Aufnahme

- **Matching:** ein pixelgenauer `TM_CCOEFF_NORMED`-Durchlauf pro Vorlage,
  ohne Pyramidensuche oder Resizing. Der Schwellwert (CLI-Default 0,90) ist
  konfigurierbar, wurde aber nie mit realen Daten kalibriert. Eine passende
  Vorlage in anderer Größe wird übersprungen oder nur als Teilbild gesucht.
- **False Positives:** konstante Vorlagen/Bildregionen haben bei
  `TM_CCOEFF_NORMED` keine aussagekräftige Varianz; Score 1.0 ist kein Beleg für
  eine Übereinstimmung. Zudem liefert der Matcher stets nur den höchsten
  Kartenkandidaten ohne Mindestabstand zum Zweitplatzierten. Ein Schwellenwert
  allein kontrolliert Ambiguität nicht.
- **Auflösung/DPI/Tische:** Regionen sind relativ zum aufgenommenen Fenster,
  was die Positionen größenabhängig skaliert. Vorlagen bleiben jedoch in ihrer
  Pixelgröße unverändert. Es gibt kein DPI-Awareness-Setup, keine
  Fenstergeometrie-Aktualisierung und keine Layoutkalibrierung pro Auflösung.
  Mehrere Monitore/teilweise verdeckte Karten sind nicht getestet.
- **Leistung:** MSS wird für jedes Bild neu geöffnet; die Hauptschleife läuft
  ohne Pause. Es gibt keine Messinstrumentierung. Ein belastbarer Durchlauf
  unter 100 ms kann mangels realer Vorlagen, Ziel-Fenster und ladbarer
  OpenCV-Laufzeit nicht bestätigt werden. Eine Qt-Overlay-Refreshzeit ist
  mangels Overlay nicht messbar.

## Pokerlogik, GUI und Logging

- **Pokerlogik:** Handwert, Draws, Outs und Odds sind nicht implementiert.
  Daher sind Pair/Two-Pair/Trips/Straight/Flush/Full-House, Draw-Kategorien,
  bekannte Situationen (einschließlich `Ah Kh` auf `Qs Js 2d`) und Odds nicht
  prüfbar, ohne ein neues Feature samt fachlichen Entscheidungen zu entwerfen.
- **GUI:** Trotz PyQt6-Abhängigkeit gibt es keine Qt-Anwendung, keinen Overlay-
  Code, keine Threads/Signals und keine Always-on-top-/Transparenzlogik.
  UI-Freezes und GUI-Race-Conditions sind im aktuellen Bestand nicht anwendbar.
  Der CLI-Erkennungslauf kann dagegen CPU belegen und die Fehlerbehandlung
  blockiert auf Terminaleingabe.
- **Logging:** Standard-Logging auf INFO und ein DEBUG-Eintrag bei
  Nichterkennung. Es fehlen Laufzeit-/Score-/Geometrie-Metriken; fehlerhafte
  Templates und einzelne fehlgeschlagene Leseoperationen werden nicht
  nachvollziehbar protokolliert.

## Priorisierte Maßnahmen

1. Projekt mit uv definieren, Python-Untergrenze deklarieren und pytest,
   pytest-cov, Ruff und mypy als Entwicklungswerkzeuge verfügbar machen.
2. Degenerierte Eingaben/Vorlagen beim Matching ablehnen und Bild-/Threshold-
   Voraussetzungen validieren; realistische synthetische Regressionstests statt
   flacher Farbflächen ergänzen.
3. Capture-Ressourcen wiederverwenden, Win32-Signaturen korrekt deklarieren und
   Capture/Erkennung messbar machen.
4. Projektgrenzen dokumentieren: für Poker, GUI, Bildqualität und Hardware-
   Performance sind zusätzliche Implementierung/Daten und Tests erforderlich.

Pokerengine, Overlay und echte Kartendaten werden nicht als Teil dieses
CV-/Capture-Fixes neu erfunden.

## Umgesetzte Korrekturen

- uv-Projekt und Lockfile angelegt; Laufzeitabhängigkeiten aus
  `requirements.txt` migriert, Python-Untergrenze auf 3.12 gesetzt und
  `pytest`, `pytest-cov`, Ruff und mypy als Dev-Abhängigkeiten ergänzt.
  `eval7` ist wegen der verifizierten fehlenden Windows-Distribution auf Linux
  x86_64 beschränkt. `requirements.txt` wurde entfernt, und die Installation
  ist in `README.md` auf uv umgestellt.
- Matcher validiert nun Schwellenwert, Kartencode und Bildformat. Leere/
  varianzlose Vorlagen werden abgelehnt; varianzlose Bildbereiche werden nicht
  als Treffer gewertet. Der Match-Score wird ausdrücklich als OpenCV-Score und
  nicht als kalibrierte Wahrscheinlichkeit behandelt.
- Regionen sind auf endliche, positive Werte innerhalb des normierten Fensters
  beschränkt. Der Detector validiert Screenshot-Form und protokolliert
  Kartencode samt Roh-Score auf DEBUG.
- Capture verwendet einen wiederverwendeten MSS- und Win32-API-Kontext,
  deklarierte Win32-Funktionssignaturen, aktualisierte Fensterkoordinaten und
  einen DPI-Awareness-Versuch im CLI. Diese Windows-API-Pfade konnten in der
  aktuellen Laufzeit nicht auf einem echten Desktop verifiziert werden.
- CLI-Schleife ist auf 20 Hz begrenzt, Fehler werden nicht mehr mit einer
  allgemeinen `except Exception`-/Eingabe-Schleife verdeckt. `--timings`
  erfasst Fensteraktualisierung, Screenshot, OpenCV-Aufrufe, Gesamterkennung
  und Zykluszeit. Vorlagen-Ausgabefehler im Generator werden gemeldet.
- Testdateien verwenden jetzt pytest und nicht konstante Musterflächen. Sie
  umfassen Template-/Detector-, Konfigurations- und Capture-Fälle. Synthetische
  Muster sind Unit-Testdaten, keine repräsentativen Tisch-Screenshots.

## Verifikation und Benchmark-Status

| Prüfung/Metrik | Ergebnis |
|---|---|
| `uv sync --locked` | erfolgreich |
| `uv run ruff check .` | erfolgreich |
| `uv run python -m compileall -q config.py main.py vision tests tools` | erfolgreich |
| Konfigurations- und Capture-Tests | 8 bestanden |
| Gesamtes `uv run pytest -q` | nicht ausführbar: OpenCV-DLL-Import wird durch die lokale Windows-Anwendungssteuerungsrichtlinie blockiert; dadurch scheitert die Collection der CV-Tests |
| `uv run python -m mypy .` | nicht ausführbar: dieselbe Laufzeitumgebung blockiert beim mypy-Start das Laden einer `base64`-DLL |
| Pylance Workspace-Diagnostik | keine Diagnosen nach den Änderungen |
| Fensteraktualisierung/Screenshot/OpenCV/Erkennung | Instrumentiert, aber kein belastbarer Zahlenwert: kein Ziel-Fenster und OpenCV kann in dieser Laufzeit nicht geladen werden |
| Gesamtziel `<100 ms` | nicht verifiziert; daher keine Performance-Behauptung |
| Overlay-Refresh | nicht anwendbar, da kein Overlay implementiert ist |
| Bildgenauigkeit/False-Positive-Rate/52 Karten | nicht messbar ohne echte Templates und reale Screenshot-Testdaten |

Die CV-Regressionstests sind implementiert, aber bis zu einem Lauf auf einem
Windows-System, auf dem OpenCV geladen werden darf, nicht als bestanden
anzusehen. Ebenso bleiben Pokerhand-/Draw-/Out-/Odds-Tests offen, bis die
Pokerlogik tatsächlich Teil des Projekts ist.
