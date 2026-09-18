# Wartungsmanagement Frontend mit Fabrik Frontend

Das Projekt enthält ein Frontend für die Wartungsmanagement Datenbank.
Die Daten werden dabei über die API Schnittstelle gelesen. Desweiteren sind
alle Anweisungen für uv enthalten um die Verfügbarkeit der benötigten Python 
Bibliotheken zu garantieren.

## Start

1. `.env.example` nach `.env` kopieren.
2. In `.env` den API Key und die Base URL eintragen.
3. Programm starten:

```bash
uv sync
cp .env.example .env
uv run python src/__main__.py
```