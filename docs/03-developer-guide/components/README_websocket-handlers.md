README – WebSocketHandler (Protokoll- und Ereignisverarbeitungsschicht)
1. Zweck der Datei

Der WebSocketHandler bildet die logische Schicht oberhalb des ConnectionManager.
Er übernimmt:

die Interpretation der eingehenden WebSocket-Nachrichten

die Zuordnung zu passenden Handlern

die Integration von Chat-Logik, Projekten, Tickets, Dateien und KI

die Verwaltung pro Verbindung/Sitzung

Der Handler arbeitet eng mit folgenden Komponenten zusammen:

MessageService

ProjectService

FileService

ConnectionManager

2. Architekturüberblick

Der Handler besteht aus drei technischen Hauptbereichen:

2.1 Sitzungsschicht (Session Layer)

Für jede Verbindung wird ein Session-Objekt verwaltet:

Feld	Bedeutung
websocket	aktive WebSocket-Instanz
username	aktueller Benutzername
user_id	optionale Benutzer-ID
rooms	Menge der aktiven Räume
connected_at	Zeitpunkt der Verbindungsannahme
last_activity	letzter Aktivitätszeitpunkt
client_info	IP/Port aus WebSocket
user_agent	Browserkennung
authenticated	Flag für Anmeldung
message_count	Anzahl verarbeiteter Nachrichten

Diese Informationen dienen der Protokollierung, Steuerung und Fehlerdiagnose.

2.2 Nachrichtenschicht (Message Dispatch Layer)

Nachrichten werden in folgende Schritte unterteilt:

Empfangen → JSON-Parsen

Validieren → Pydantic‐Modell (WebSocketMessage)

Identifizieren anhand des type-Felds

Weiterleitung an registrierte Handlerfunktionen

Der Handler besitzt eine zentrale Routingtabelle:

self.message_handlers = {
    "chat_message": self._handle_chat_message,
    "user_typing": self._handle_typing_indicator,
    "user_join": self._handle_user_join,
    "user_leave": self._handle_user_leave,
    "room_join": self._handle_room_join,
    "room_leave": self._handle_room_leave,
    "ai_request": self._handle_ai_request,
    "file_upload_request": self._handle_file_upload_request,
    "project_update": self._handle_project_update,
    "ticket_update": self._handle_ticket_update,
    "ping": self._handle_ping,
    "authentication": self._handle_authentication
}


Nur Nachrichten mit bekannten Typen werden akzeptiert.

2.3 Lebenszyklus- und Hintergrundprozesse

Folgende Mechanismen laufen parallel zur Kommunikation:

Heartbeat-Überwachung (alle 30 Sekunden)

Timeout-Handling beim Empfangen

Überprüfung der Verbindung per Ping

Fehlerbehandlung und Sitzungsbereinigung

Diese zusätzlichen Kontrollen sollen eine stabile WebSocket-Sitzung sicherstellen.

3. Verbindungsablauf
3.1 Verbindungsaufbau

Beim Herstellen einer WebSocket-Verbindung führt der Handler folgende Schritte aus:

Übergibt die Verbindung an den ConnectionManager

Initialisiert interne Sessiondaten

Sendet ein strukturiertes „Welcome Package“

Übermittelt die letzten gespeicherten Nachrichten

Startet die Nachrichtenverarbeitungsschleife

3.2 Nachrichtenverarbeitungsschleife

Die Hauptschleife:

wartet asynchron auf eingehende Daten

überwacht Zeitüberschreitungen

verarbeitet Nachrichtentypen über _process_message()

stoppt bei Verbindungsabbruch oder Fehlern

3.3 Verbindungsabbau

Beim Abbruch:

Entfernen aus allen Räumen

Senden optionaler „offline“-Benachrichtigung

Löschen der Sessiondaten

Entfernen über manager.disconnect()

4. Nachrichtentypen und Handler
4.1 Chatnachrichten (chat_message)

Validierung von Benutzername und Nachricht

Speicherung über MessageService

Weiterleitung an Raum oder globale Nutzer

optionale KI-Autoantwort

Bei Räumen wird der Versand gezielt auf die Mitglieder begrenzt.

4.2 AI-Anfragen (ai_request)

Die Schritte:

Optionale Kontextabfrage

Übergabe an MessageService → AI-Modell

Speicherung der KI-Antwort

Rücksendung an den anfragenden Client

Fehler werden als strukturierte Fehlermeldungen gesendet.

4.3 Raumbeitritte / Raumverlassen (room_join, room_leave)

Die Funktionen:

Hinzufügen/Entfernen aus einer Raumgruppe

Bestätigungsnachricht an den Client

optionaler Status-Broadcast (Benutzer betritt/verlässt Raum)

4.4 Authentifizierung (authentication)

Übergabe an manager.authenticate_user()

Aktualisieren der Sessiondaten

Bereitstellen eines Bestätigungspakets

optionaler Broadcast über Online-Status

4.5 Tippen-Indikator (user_typing)

Weitergabe einer „typing“-Nachricht an Raum oder globale Empfänger

4.6 Projekt- und Ticket-Updates (project_update, ticket_update)

Die Funktionen sind vorbereitet und akzeptieren die Daten, leiten aber derzeit intern nichts weiter.

4.7 Datei-Upload-Anfragen (file_upload_request)

Der Handler:

meldet den Empfang

generiert Upload-Metadaten

sendet ein Upload-Autorisierungspaket

Zuständig für den eigentlichen Upload bleibt ein HTTP-Endpoint.

4.8 Ping/Pong (ping)

Rücksendung einer „pong“-Nachricht

Aktualisierung der Aktivität

5. Fehlerbehandlung

Bei Fehlern werden strukturierte Meldungen versendet:

{
  "type": "error",
  "message": "...",
  "timestamp": "...",
  "error_code": "optional"
}


Der Code vermeidet unkontrolliertes Schließen der Verbindung und protokolliert alle Fehler über enhanced_logger.

6. Integrationen
6.1 MessageService

Speichern

AI-Generierung

Kontextauswertung

6.2 ProjectService

künftige Projekt-Events

6.3 FileService

künftige Datei-Uploadsteuerung

6.4 ConnectionManager

alle physischen Verbindungsoperationen

Raumsteuerung

Benutzerzuordnung

Überwachung

7. Überwachungs- und Analysefunktionen

Der Handler bietet eine eigene Methode:

get_connection_stats()


Sie liefert:

Anzahl der Sitzungen

Anzahl authentifizierter Nutzer

Metadaten pro Verbindung

Verweis auf die Statistiken des ConnectionManagers

Damit lässt sich jederzeit ein Gesamtstatus erzeugen.

8. Zusammenfassung

Der WebSocketHandler bildet die Protokoll- und Ereignisverarbeitungsschicht für WebSocket-Kommunikation.
Er übernimmt:

Routing aller eingehenden Nachrichten

Verbindungs- und Sitzungspflege

Chat- und Raumfunktionen

optionale Künstliche-Intelligenz-Integration

Übertragung projekt- und dateibezogener Signale

Der Handler ergänzt damit den reinen Verbindungsmanager um Anwendungslogik und Datenverarbeitung.