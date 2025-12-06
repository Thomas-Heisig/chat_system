README – EnhancedChatApp (Frontend-Logik)

Datei: static/js/chat.js
Klasse: EnhancedChatApp

1. Zweck

Die Klasse EnhancedChatApp stellt die gesamte clientseitige Steuerungslogik des Web-Frontends bereit.
Sie ist verantwortlich für:

Aufbau und Überwachung der WebSocket-Verbindung

Darstellung und Verarbeitung eingehender Nachrichten

Senden von Chat-, Raum-, AI- und Statusinformationen

Aktualisierung der Benutzeroberfläche

Verwaltung lokaler Zustände (Username, Sprache, Theme, Räume usw.)

Aufrufe der REST-API (Projekte, Tickets, Dateien)

Interaktion mit Modals und UI-Komponenten

Die Datei enthält keine Geschäftslogik im klassischen Sinn, sondern bildet die visuelle Schicht und das Verhalten des Frontends ab.

2. Initialisierung

Beim Laden des Dokuments (window.onload) wird:

Eine Instanz von EnhancedChatApp erzeugt

Das Theme gesetzt

Übersetzungen angewendet

DOM-Events gebunden

WebSocket-Verbindung aufgebaut

Initiale Daten geladen

Benutzerstatistiken aktualisiert

Die Konstruktion setzt Standardwerte:

Variable	Zweck
username	Lokaler Name
ws	WebSocket-Instanz
isConnected	Verbindungsstatus
reconnectAttempts	Zähler für Wiederverbindungen
currentRoom	Aktiver Chatraum
typingUsers	Menge aktuell tippender Benutzer
onlineUsers	Menge erkannter Benutzer
projects / tickets / files	Cache der API-Daten

Die Datei lädt außerdem Übersetzungsobjekte für Deutsch und Englisch.

3. Interne Struktur des Moduls

Die Klasse lässt sich funktional in folgende Hauptmodule gliedern:

3.1 Verbindungsmanagement

connectWebSocket()

updateConnectionStatus()

Reconnect-Mechanismus mit exponentiellem Backoff

Error-Handling für onclose / onerror

Verarbeitung eingehender WebSocket-Events

3.2 Chat & Nachrichtenfluss

sendMessage()

handleIncomingMessage()

addChatMessage()

addSystemMessage()

handleKeyPress()

loadRoomMessages()

3.3 Raumverwaltung

switchRoom()

joinRoom()

addRoomToUI()

Room-Modals

3.4 Benutzerverwaltung

setUsername()

trackUserActivity()

updateOnlineUsers()

updateUserStats()

3.5 AI-Modul

sendAIMessage()

addAIMessage()

removeLastAIMessage()

handleAIResponse()

openAIAssistant()

3.6 UI-Steuerlogik

switchSection()

applyTheme()

applyTranslations()

showModal() / closeModals()

showNotification()

Emoji-Picker (Platzhalter)

3.7 REST-API-Interaktion

apiCall(endpoint)

loadInitialData()

loadProjects()

loadFiles()

loadTickets()

4. WebSocket-Protokoll (Clientseite)

Der Client sendet folgende Nachrichtentypen:

Typ	Zweck
chat_message	Nachricht in aktuellem Raum
user_typing	Tippstatus
join_room	Raum betreten
ai_request	AI-Frage senden
authentication	Benutzeranmeldung (optional, falls implementiert)

Der Client verarbeitet folgende eingehenden Typen:

Typ	Bedeutung
chat_message	Chatnachricht
user_joined	Benutzer online
user_left	Benutzer offline
user_typing	Tipp-Indikator
room_joined	Bestätigung Raumbeitritt
room_created	Neuer Raum wurde angelegt
ai_response	Antwort der KI
error	Fehler vom Backend

Wichtig:
Die Struktur ist passend zu WebSocketHandler auf Serverseite, jedoch leicht vereinfacht, da das Frontend nicht alle serverseitigen Daten nutzt.

5. Verbindungsmechanismus & Zustände
5.1 Aufbau
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws`;
this.ws = new WebSocket(wsUrl);

5.2 Reconnect-Strategie

maximal 5 Versuche

exponentielle Verzögerung: 1000 * 2^n, gekappt auf 30 Sekunden

erneuter Verbindungsversuch nur bei nicht-cleanem Abbruch

5.3 Statusbereiche, die stets aktualisiert werden

Connection Bar

Sidebar Status

Message Input (enabled/disabled)

6. Chat- und Eingabemechanik
6.1 Senden

Nachrichten werden als JSON gesendet:

{
  "type": "chat_message",
  "username": "<name>",
  "message": "<text>",
  "room": "<currentRoom>",
  "timestamp": "<ISO>"
}

6.2 Anzeige

Nachrichten werden als eigene oder fremde Nachricht dargestellt.
Raumfilterung sorgt dafür, dass nur Nachrichten des aktiven Raums angezeigt werden.

7. Tipp-Indikator

Der Client sendet:

{
  "type": "user_typing",
  "username": "...",
  "typing": true/false,
  "room": "<currentRoom>"
}


Eingehende Indikatoren werden in typingUsers gespeichert.
Anzeige:

max. 3 Benutzer

automatische Bereinigung bei Inaktivität

8. Räume

Die Klasse unterstützt:

Erstellen neuer Räume (Modal)

Wechsel zwischen Räumen

Laden der letzten 50 Nachrichten pro Raum

UI-Aktualisierung der Raumliste

Die Logik ist mit dem WebSocket-Flow kompatibel, die serverseitige Umsetzung definiert den tatsächlichen Raum-Scope.

9. AI-Modul
9.1 Ablauf

Benutzer fragt über /api/ai/ask an

"Thinking..."-Nachricht wird angezeigt

Backend liefert Antwort

Anzeige der AI-Antwort

9.2 Datenformat
{
  "question": "...",
  "username": "...",
  "use_context": true
}


Die Anzeige erfolgt ohne HTML-Interpretation, alles wird escaped.

10. Projektsystem, Tickets, Dateien

Diese Bereiche:

laden Daten über REST-API

rendern UI-Grid-Elemente

aktualisieren Badges in der Navigation

Da die vollständige Back-End-API im Frontend nur teilweise genutzt wird, sind viele Funktionen vorbereitet, aber modular erweiterbar.

11. Sicherheitsaspekte im Frontend

Alle Benutzereingaben werden mit escapeHtml() maskiert

Es erfolgt keine Eigeninterpretation von HTML

JSON-Parsing wird gefangen

Fehler werden protokolliert und angezeigt

Keine Speicherung sensibler Daten im LocalStorage

12. Fehlerbehandlung

Der Client behandelt:

WebSocket-Abbrüche

API-Fehler (response.ok === false)

JSON-Parsing

ungültige Eingaben (zu lange Namen/Nachrichten)

fehlende UI-Elemente

Der Anwender erhält in den meisten Fällen eine sichtbare Benachrichtigung.

13. Zusammenfassung des Frontend-Datenflusses
Eingang → UI

WebSocket-Nachricht → handleIncomingMessage() → Darstellung im Chat

REST-API-Antwort → Rendering von Projekten, Tickets, Dateien

Benutzeraktionen → UI-Update sofort

Ausgang → Server

Chatnachricht → WebSocket

Typing → WebSocket

Raumwechsel → WebSocket

AI-Frage → REST (POST)

Projekt/Ticketaktionen → REST

14. Erweiterbarkeit

Die Klasse lässt folgende Erweiterungen ohne große Umstrukturierung zu:

zusätzliche Nachrichtentypen

weitere Räume

weitere Sprachen

zusätzliche Module (Kanbanboard, Datei-Vorschau)

Nutzung eines State-Managers (optional)