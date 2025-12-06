📘 README – FastAPI Router (Chat, Projekte, Tickets, Dateien, KI, WebSockets)
Zweck der Datei

Diese Datei definiert sämtliche HTTP- und WebSocket-Routen für das System.
Sie stellt die zentrale Schnittstelle zwischen:

Frontend

Backend-Services

Datenbank-Repositories

KI-Komponenten

Datei-Upload

Projekt- & Ticket-Management

Statistiken & Systeminformationen

dar.

Der Router wird in FastAPI registriert und steuert dadurch alle Anfragen.

Gesamtarchitektur

Der Router nutzt folgende Schichten:

Services

MessageService

ProjectService

FileService

→ Geschäftslogik

Repositories

direkter Zugriff auf SQLite

Modelle

Pydantic-Modelle für Validierung

WebSocketHandler

verwaltet Echtzeitkommunikation

1. Initialisierung

Beim Import werden erstellt:

alle Repository-Instanzen

alle Service-Instanzen

WebSocket-Handler

Fehler beim Laden werden geloggt.

Es wird zusätzlich geprüft, welche Features aktiviert sind:

Projektmanagement

Ticketsystem

Datei-Uploads

Authentifizierung

RAG / KI

Diese Flags stammen aus der Settings-Konfiguration.

2. HTML-Routen
GET /

Liefert die Hauptseite (index.html).
Bei Fehlern: HTTP-500.

GET /projects

Lädt die Projektseite (projects.html).
Fällt zurück auf die Startseite, wenn Template fehlt.

3. WebSocket
WebSocket /ws

Startet die Echtzeitkommunikation.

Der WebSocketHandler übernimmt:

Eintreffende Nachrichten

Broadcast

Projekt- und Raumkontext

KI-Antworten, falls aktiviert

Verbindungen und Fehler werden protokolliert.

4. System & Health
GET /health

Liefert eine strukturierte Systemdiagnose:

KI aktiviert?

verfügbare KI-Modelle

Datenbankverbindung

Feature-Flags

GET /info

Listet alle Routen kategorisiert auf:
Pages, WebSocket, KI, Projekte, Tickets, Files, Suche, Statistiken.

5. KI-Endpunkte
GET /api/ai/models

Gibt verfügbare Modelle zurück:

Ollama

Custom

POST /api/ai/ask

Stellt eine Frage an die KI. Parameter:

Frage

Benutzername

Kontext verwenden?

Modelltyp

Projektkontext

Das Ergebnis enthält:

Antwort

genutzten Kontext

Quellen (bei RAG)

Fehler werden kontrolliert als HTTP-Exceptions ausgegeben.

6. Projekt-Endpunkte

Nur aktiv, wenn Feature aktiviert ist.

GET /api/projects

Filter:

Status

Ersteller

Mitglied

Pagination

POST /api/projects

Legt ein neues Projekt an.
Unterstützt Tags & Fälligkeitsdatum.

GET /api/projects/{id}

Platzhalter – gibt strukturierte Musterantwort aus.

7. Ticket-Endpunkte

Wie bei Projekten sind Feature-Flags erforderlich.

GET /api/tickets

Filter:

Projekt

Status

Priorität

Verantwortlicher

POST /api/tickets

Neues Ticket mit:

Titel

Beschreibung

Priorität

Typ

Fälligkeitsdatum

POST /api/tickets/{id}/assign

Zuweisung eines Tickets an einen Benutzer.

GET /api/projects/{project_id}/tickets

Zeigt alle Tickets eines Projekts.

8. Datei-Endpunkte

Feature-abhängig.

POST /api/files/upload

Unterstützt:

Metadaten

optionalen Projekt- oder Ticketbezug

Background-Task für Analyse

Dateigrößenbegrenzung (aus Settings)

GET /api/files/{id}

Gibt Metadaten zurück.

GET /api/files/{id}/download

Download + Erhöhung des Download-Counters.

9. Nachrichten-Endpunkte
GET /api/messages/filter

Umfangreicher Filtermechanismus:

Benutzername

Nachrichtentyp

Raum

Projekt

Ticket

Zeitraum

Textsuche

AI-Flag

Pagination

Die Daten kommen aus dem MessageRepository.

10. Suche & Statistik-Endpunkte
GET /api/search

Durchsucht:

Nachrichten

Projekte

Tickets

Dateien

GET /api/stats

Aggregierte Kennzahlen:

Benutzer

Projekte

Tickets

Räume

Nachrichten

AI-Nachrichten

Verteilung von Statuswerten

Aktivität der letzten 24h

GET /api/ai/stats

Wertet KI-Interaktionen aus.

11. System-Konfiguration
GET /api/system/configuration

Gibt systemweite Einstellungen zurück:

KI

Sicherheit

Dateien

Features

Limits

Fazit

Der Router bildet die zentrale API-Schicht des Systems und verbindet:

Frontend

KI

Projektverwaltung

Ticketsystem

Dateispeicher

Suchsystem

Echtzeitkommunikation

Die Datei ist umfangreich, aber klar modularisiert:

Jede Funktionsgruppe besitzt eigene Routen.

Services kapseln die Logik.

Repositories kapseln den Datenzugriff.