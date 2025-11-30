README – main.py (FastAPI Hauptanwendung)
1. Zweck der Datei

Die Datei main.py bildet den Einstiegspunkt der gesamten Anwendung.
Sie übernimmt folgende Funktionen:

Erstellung und Konfiguration der FastAPI-App

Initialisierung der Datenbank

Einrichtung von Middlewares

Registrierung der API-Routen

Setzen von Sicherheits-Headern

Bereitstellung umfassender Health-Checks und Status-Endpunkte

Lebenszyklusverwaltung (Startup / Shutdown)

Optionaler Betrieb über Uvicorn (falls direkt ausgeführt)

2. Aufbau und Ablauf
2.1 Lifespan-Manager

Die Anwendung nutzt einen asynchronen Kontextmanager, um den Start- und Stoppvorgang kontrolliert auszuführen.

Beim Startup werden folgende Schritte ausgeführt:

Logeintrag mit App-Name, Version, Environment

Initialisieren der Datenbank (init_database())

Kontrolle der Datenbankintegrität (check_database_health())

Protokollieren der aktiven Features

Messung der Startup-Zeit

Beim Shutdown:

Berechnung der Shutdown-Zeit

Abrufen von Datenbankstatistiken

Loggen aller Endwerte (Nachrichten, Projekte, Tickets, Dateien)

3. FastAPI-Konfiguration

Beim Erstellen des FastAPI-Objekts werden u. a. gesetzt:

Titel, Version, Kontaktinformationen

API-Dokumentation (nur im Debug-Modus aktiv)

Lizenzinformationen

HTML-Beschreibung der Funktionalität

Lifespan-Funktion

Tags für einzelne Bereiche

OpenAPI-Pfad im Debug-Modus

Die Anwendungsbeschreibung beinhaltet:

Chat

AI-Funktionen

Projekte

Tickets

Dateiupload

Suchfunktionen

Nutzerverwaltung

4. Middleware
4.1 CORS Middleware

Konfiguriert anhand der Werte aus dem Settings-Objekt:

erlaubte Ursprünge

erlaubte Methoden

Header

Exposed-Header

4.2 Logging Middleware

Jeder Request wird mit folgenden Daten protokolliert:

Startzeit

Request-ID

Methode

URL

User-Agent

Dauer

Antwortgröße

Antworten erhalten zusätzliche Header:

X-Process-Time

X-Request-ID

4.3 Security-Header Middleware

Folgende Header werden gesetzt:

X-Content-Type-Options

X-Frame-Options

X-XSS-Protection

Strict-Transport-Security

Content-Security-Policy

Referrer-Policy

Permissions-Policy

Diese Werte sind fest definiert und folgen üblichen Empfehlungen.

5. Exception-Handler
5.1 HTTPException-Handler

Gibt strukturierte JSON-Fehler zurück:

Fehlernachricht

Statuscode

Pfad

Methode

Zeitstempel

Zusätzlich: Header X-Error-Type: HTTPException.

5.2 Globaler Fehlerhandler

Fängt alle nicht behandelten Fehler:

Protokolliert Fehlertyp und Traceback (nur im Debug-Modus)

Antwort mit Statuscode 500

Header X-Error-Type: InternalServerError

6. Static-File-Routing

Es werden folgende Verzeichnisse gemountet, sofern vorhanden:

Route	Ordner	Zweck
/static	static	statische Assets
/uploads	uploads	hochgeladene Dateien
/docs	docs	Dokumentationen

Diese Mounts sind optional und werden nur erstellt, wenn der jeweilige Ordner existiert.

7. Routing

Es werden folgende Router eingebunden:

Router	Prefix	Bereich
chat_router	``	Chat UI / WebSocket
messages_router	/api	REST-API für Nachrichten

Die Zuordnung erfolgt über eine Konfigurationsliste.

8. Überwachungs- und Diagnose-Endpunkte
8.1 /health

Stellt einen umfassenden Systemstatus bereit:

Datenbankstatus

Anzahl der Einträge in allen Tabellen

AI-Status (konfigurationsbasiert)

Feature-Status

Systeminformationen (Python Version, Plattform, Log-Level)

8.2 /status

Technischer Status zur Überwachung:

Datenbankstatistiken

Uptime

Datei-Limits

Konfigurationseinträge

8.3 /

Root-Endpoint mit Metadaten über:

Zweck der App

Features

Dokumentationslinks

Endpunkte

Support-Informationen

8.4 Debug-Endpunkte (nur im Debug-Modus)

/debug/config – Ausgabe der geladenen Settings

/debug/routes – Liste aller registrierten Routen

9. Betrieb über Uvicorn

Falls die Datei direkt ausgeführt wird (if __name__ == "__main__"):

Start des Uvicorn-Servers

Host, Port, Reload usw. aus Settings

Einschränkung: Bei aktivem Reload wird Worker-Anzahl auf 1 begrenzt

10. Zusammenfassung

main.py übernimmt sämtliche zentralen Systemaufgaben:

Lifecycle-Management

API-Konfiguration

Logging und Sicherheit

Ausnahmebehandlung

Routing

Monitoring

Die Datei ist modular aufgebaut und greift auf externe Services und Repositories zurück. Alle Funktionsbereiche sind unabhängig voneinander strukturiert und lassen sich isoliert erweitern.