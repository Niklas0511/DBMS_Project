# Wartungsmanagement mit FastAPI und PostgreSQL

Das Projekt startet zwei Container: eine PostgreSQL-Datenbank und eine
FastAPI-Anwendung. Das Schema wird beim ersten Erzeugen des Datenbank-Volumes
automatisch geladen.

## Start

1. `.env.example` nach `.env` kopieren.
2. In `.env` ein sicheres Passwort eintragen.
3. Container bauen und starten:

```bash
cp .env.example .env
docker compose up --build -d
```

Danach stehen folgende Seiten bereit:

- API-Dokumentation: http://localhost:8000/docs
- Zustandsprüfung: http://localhost:8000/health

## Wichtige Befehle

```bash
# Logs anzeigen
docker compose logs -f

# Container stoppen
docker compose down

# Container stoppen und Datenbank-Volume löschen
docker compose down -v
```
