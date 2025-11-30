📘 README – Daten- und Validierungsmodelle (Pydantic)
Übersicht

Die Datei stellt sämtliche Pydantic-Modelle bereit, die für das Backend benötigt werden.
Sie bildet das gemeinsame Datenmodell für:

Chat-Nachrichten

Benutzer

Projekte

Tickets

Dateien

Räume und Raum-Mitglieder

KI-Konfigurationen

WebSocket-Nachrichten

Filtermodelle

Pagination

Hilfsfunktionen zum Erstellen typischer Instanzen

Die Modelle definieren Datenstruktur, Validierung, Standardwerte und Serialisierung.
Sie sind für FastAPI kompatibel und können sowohl in REST- als auch WebSocket-Endpunkten verwendet werden.

Inhaltsverzeichnis

Zweck der Datei

Enums

Basis-Konfiguration

Modelle

Message

User

Project

Ticket

File

ChatRoom

RoomMember

MessageReaction

AIConversation

AIModel

Hilfsfunktionen

Filtermodelle

Responsemodelle

WebSocket-Modelle

Besondere Implementierungsmerkmale

Zweck der Datei

Die Datei dient als zentrale Typdefinition für das Backend.
Alle Daten, die zwischen API, Datenbank und WebSocket übertragen werden, basieren auf diesen Modellen.
Sie unterstützen:

Validierung aller Eingaben

automatische Datums-Serialisierung

Fehlervermeidung durch feste Enums

reproduzierbares, einheitliches Verhalten

saubere Schnittstellen für Frontend und Backend

Die Modelle kapseln keine Datenbanklogik – sie definieren ausschließlich Datenstrukturen.

Enums

Die Datei enthält mehrere Enumerationen, die feste und überprüfbare Werte definieren, z. B.:

MessageType – user, ai, system, command, notification

AIModelType – ollama, custom, openai, huggingface, anthropic

TicketStatus, TicketPriority, TicketType

ProjectStatus

UserRole, RoomRole

FileType

Diese Enums verhindern fehlerhafte Eingaben und erleichtern Filterlogik.

Basis-Konfiguration

Alle Modelle erben von:

class BaseDatabaseModel(BaseModel)


Wichtige Eigenschaften:

Enum-Werte werden als String gespeichert

Datumsfelder werden ISO-konform serialisiert

Eingabetexte werden automatisch von Leerzeichen bereinigt

Modelle unterstützen Namen über Alias

Dies sorgt für konsistente Serialisierung in REST- und WebSocket-Nachrichten.

Modelle

Nachfolgend die Kernmodelle mit einer sachlichen Beschreibung.

📌 Message

Ein Modell für Chatnachrichten mit Unterstützung von:

Threading (parent_id)

Räumen (room_id)

Projekt- und Ticketbezug

KI-Funktionen: Modellname, RAG-Daten, Sentiment, Kontext

Edit-Historie

komprimierbare Nachrichtentexte

WebSocket-Ausgabeformat (to_websocket_format())

Validierungen:

Benutzername darf nur bestimmte Zeichen enthalten

Nachrichten müssen Text enthalten

Automatische Werte:

Zeitstempel bei Erstellung

Standardwerte für Typ, AI-Flags und Metadaten

📌 User

Benutzermodell für Registrierung und Authentifizierung.

Wesentliche Felder:

ID (UUID)

Benutzername (validiert, nur [a-zA-Z0-9_])

E-Mail (validiert)

Hash des Passworts

Rollenmodell

Timestamps

Zusatzfunktionen:

sichere Ausgabe ohne Passwort (to_safe_dict())

Aktualisierung des Login-Zeitpunkts

📌 Project

Projektmodell mit:

Statuswerten

Mitgliedsliste

Tags, Metadaten

Statistikfeldern (Ticketanzahl, Fortschritt)

Fortschrittsberechnung

Automatische Timestamps.

📌 Ticket

Ticketmodell für Aufgaben-, Bug- und Projektsystem.

Wichtige Bereiche:

Status, Priorität und Typ

Beziehungen (Zuweisung, Projekt, verwandte Tickets)

Zeitstempel für Erstellung, Bearbeitung und Abschluss

Stundenangaben

Methoden zur Statusänderung (mark_resolved(), reopen())

📌 File

Dateiobjekt mit:

Originalnamen

Serverpfad

MD5-Hash

MIME-Type

Typklassifizierung (Dokument, Audio, Code usw.)

Downloadzähler

Kontext (Projekt, Ticket, Message)

Die Methode get_file_extension() ermöglicht Dateitypzuordnung.

📌 ChatRoom

Modell für Chatkanäle mit:

Rollenbeschränkungen

Mitglieder- und Nachrichtenstatistik

Moderationsoptionen

Archivstatus

can_user_join() prüft Zugangsrechte.

📌 RoomMember

Mitgliedschaft in Räumen, mit:

Mitgliedsrolle

Zeitpunkt letzter Aktivität

Notifikationseinstellungen

📌 MessageReaction

Reaktionen (Emojis) auf Nachrichten.

📌 AIConversation

Konversationskontext für KI-Anfragen, inkl.:

Titel

zugeordneter Benutzer

Modellpräferenzen

Metadaten

Nachrichtenzähler

📌 AIModel

Modelldefinition für konfigurierbare KI-Modelle:

Modellname

Typ (Ollama etc.)

Anbieter

Token-Kosten

Rate-Limits

Konfigurationsobjekt

Fähigkeitenliste

Hilfsfunktionen

Die Datei enthält mehrere Factory-Funktionen:

create_message()

create_ai_message()

create_user()

create_project()

create_ticket()

create_file()

Vorteile:

alle Pflichtfelder automatisch gesetzt

Standardwerte korrekt gepflegt

weniger Wiederholungen im Code

Filtermodelle

Für Abfragen implementiert:

MessageFilter

Filtert nach:

Benutzer

Typ

Zeitraum

Räumen

Projekt & Ticket

Textinhalt

Pagination

ProjectFilter

Status

Tags

Mitgliedschaft

TicketFilter

Status

Priorität

Typ

Zugewiesener Nutzer

Responsemodelle
PaginatedResponse

Bietet:

Liste der Ergebnisse

Gesamtanzahl

Seitenanzahl

Größe pro Seite

SearchResults

Zusammenfassung unterschiedlicher Suchtypen:

Nachrichten

Projekte

Tickets

Dateien

WebSocket-Modelle
WebSocketMessage

Einheitliches Format:

Typ

Daten

Zeitstempel

ChatMessageData

Spezifisches Format für Chatnachrichten im WebSocket.

TypingIndicatorData

„Benutzer tippt“-Ereignisse.

Besondere Implementierungsmerkmale

Automatische Zeiterstellung für alle Modelle

Klare Trennung zwischen REST-Format und WebSocket-Format

Validierung sämtlicher Felder

Nutzung der Pydantic-Konfiguration für konsistente Serialisierung

Einteilung in klare Modelle statt gemischter Strukturen

Factory-Funktionen für standardisierte Instanziierung