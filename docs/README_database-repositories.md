📘 README – Repository-Schicht (Datenzugriffslogik)
Übersicht

Die Datei implementiert sämtliche Repository-Klassen für den Datenzugriff auf SQLite.
Alle Datenbankoperationen – Lesen, Schreiben, Filtern und Aggregieren – erfolgen über diese Repository-Schicht.

Die Struktur trennt:

Modelle (Pydantic) → Daten- und Validierungsebene

Repositorys → CRUD-Logik und SQL-Abfragen

Datenbankverbindung → Verbindungspooling, WAL, Fehlerbehandlung

Die Repositorys sind so aufgebaut, dass sie unabhängig von der API und vom WebSocket nutzbar sind.

Inhalt der Datei

Die Datei enthält folgende Repository-Klassen:

MessageRepository

UserRepository

ProjectRepository

TicketRepository

FileRepository

SearchRepository

StatisticsRepository

Jede Klasse kapselt den kompletten Datenbankzugriff für ihr jeweiliges Modell.

1. MessageRepository
Zweck

Verwaltet sämtliche Chatnachrichten einschließlich:

normale Nachrichten

AI-generierte Antworten

Projekt- und Ticketbezug

Räume und Threads

Reaktionen (Emojis)

Filterfunktionen

Kontextdaten für KI

RAG-Daten

Edit-Historien

Wichtige Methoden
save_message(message: Message) → int

Speichert Nachrichten mit allen Metadaten.

Konvertiert Listen/Dicts in JSON.

Loggt Dauer, Erfolg oder Fehler.

get_message(id)

Gibt eine einzelne Nachricht anhand der ID zurück.

get_recent_messages(limit, room_id, project_id)

Holt aktuelle Nachrichten mit optionalen Filtern.

get_messages_by_filter(MessageFilter)

Unterstützt komplexe Filter:

Benutzername

Nachrichtentyp

Zeitraum

Räume

Projekt

Ticket

Textsuche

AI-Flag

Pagination

Gibt ein PaginatedResponse-Objekt zurück.

add_message_reaction(message_id, user_id, reaction)

Speichert Emoji-Reaktionen und erhöht Zähler.

get_message_reactions

Liest alle Reaktionen zu einer Nachricht.

_row_to_message(row)

Interne Hilfsfunktion zur Rekonstruktion eines Message-Modells aus der SQLite-Row.

Besonderheiten

Alle JSON-Felder aus der DB werden sauber decodiert.

Fehlertolerante Rückgabe, Logging über enhanced_logger.

2. UserRepository
Zweck

Verwaltet Benutzer, inkl.:

Registrierung

Login-Zeitpunkte

Profildaten

Methoden
create_user(user)

Speichert Benutzer unter Verwendung der Pydantic-Felder.

get_user_by_id
get_user_by_username

Einfacher Zugriff auf Benutzer.

update_user_last_login

Aktualisiert Anmeldezeitpunkt.

3. ProjectRepository
Zweck

Verwaltet Projektobjekte.

Methoden
create_project(project)

Legt ein Projekt an.

get_projects_by_filter(ProjectFilter)

Unterstützte Filter:

Status

Ersteller

Mitglieder (via JSON-Abfrage)

Gibt PaginatedResponse zurück.

_row_to_project(row)

Rekonstruiert ein Pydantic-Projektmodell.

4. TicketRepository
Zweck

Abbildung der Ticketverwaltung.

Methoden
create_ticket(ticket)

Speichert Ticket und erhöht ticket_count im zugehörigen Projekt.

get_tickets_by_filter(TicketFilter)

Filtert nach:

Status

Typ

Priorität

Projekt

Bearbeiter

Ersteller

_row_to_ticket(row)

Konvertiert Datenbank->Modell.

5. FileRepository
Zweck

Verwaltet hochgeladene Dateien, inkl.:

Dateimetadaten

Hash

Zuordnung zu Projekten/Tickets/Messages

Downloadzähler

Methoden
save_file(file)

Speichert Datei-Metadaten.

get_file(file_id)

Liest Dateiobjekt.

increment_download_count

Erhöht Zähler nach Download.

_row_to_file(row)

Konvertiert Datenbankzeilen.

6. SearchRepository
Zweck

Zentrale Suchfunktion über mehrere Modelle hinweg.

Durchsuchte Bereiche:

Nachrichten (Textsuche)

Projekte (Name, Beschreibung)

Tickets (Titel, Beschreibung)

Dateien (Name, Beschreibung)

Methode
global_search(query, limit)

Gibt SearchResults zurück.

Die Suchergebnisse werden proportional über die Kategorien verteilt, um breite Ergebnisse zu ermöglichen.

7. StatisticsRepository
Zweck

Sammelt statistische Kennzahlen über das Gesamtsystem:

Anzahl Nutzer, Projekte, Tickets, Dateien, Räume

Anzahl Nachrichten

Anzahl AI-Nachrichten

Anzahl aktiver Benutzer

Nachrichten der letzten 24 Stunden

Verteilung der Projekt- und Ticketstatus

Methode
get_system_statistics()

Führt mehrere aggregierte SQL-Abfragen aus.

Gibt ein strukturiertes Dictionary zurück.

Besondere Implementierungsmerkmale

Strikte Trennung von Datenmodell und Datenbankzugriff

Konsequente Nutzung von Pydantic zur Validierung

JSON-Felder werden systematisch codiert und decodiert

Robuste Fehlerbehandlung

Einsatz des zentralen enhanced_logger

Volle Unterstützung für AI-bezogene Datenfelder

Pagination sauber implementiert

Filter werden dynamisch zu SQL zusammengebaut

Fazit

Diese Datei stellt die vollständige Repository-Schicht dar, die alle Operationen mit SQLite abbildet.
Sie bildet die Grundlage für:

REST-API

WebSocket-Kommunikation

KI-Logik

Projekt- und Ticketsystem

Dateiverwaltung

Suche und Statistiken