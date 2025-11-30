Chat System – API Dokumentation
1. Überblick

Diese Dokumentation beschreibt die HTTP- und WebSocket-Schnittstellen des Chat-Systems.
Die REST-API bietet Lesezugriffe auf Nachrichten und Statusinformationen.
Die WebSocket-Schnittstelle ermöglicht bidirektionale Echtzeitkommunikation.

2. Health- und Status-Endpunkte
GET /health

Einfacher Funktionsnachweis.

Beispiel-Response

{
  "status": "healthy",
  "app": "Chat System",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0"
}

GET /status

Erweiterte Systeminformationen.

Beispiel-Response

{
  "status": "healthy",
  "app": "Chat System",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "database": {
    "message_count": 150,
    "status": "connected"
  },
  "websocket": {
    "active_connections": 5,
    "status": "active"
  },
  "system": {
    "uptime": "2 hours",
    "memory_usage": "45%"
  }
}

3. Nachrichten-Endpunkte
GET /api/messages

Abruf aller Nachrichten in chronologischer Reihenfolge.

Query-Parameter

Parameter	Typ	Beschreibung
limit	optional	Maximale Anzahl
offset	optional	Pagination-Startwert

Beispiel-Response

{
  "messages": [
    {
      "id": 1,
      "username": "Benutzer",
      "message": "Hallo Welt",
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}

GET /api/messages/recent

Abruf der letzten Nachrichten.

Query-Parameter

Parameter	Typ	Beschreibung
limit	optional	Standard: 50, Maximum: 100

Beispiel-Response

{
  "messages": [
    {
      "id": 1,
      "username": "Benutzer",
      "message": "Hallo Welt",
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "total": 50,
  "limit": 50
}

GET /api/messages/user/{username}

Abruf der Nachrichten eines bestimmten Benutzers.

Path-Parameter

Parameter	Typ
username	Zeichenkette

Query-Parameter

Parameter	Typ
limit	optional

Beispiel-Response

{
  "messages": [
    {
      "id": 1,
      "username": "max_mustermann",
      "message": "Hallo zusammen!",
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "username": "max_mustermann",
  "total_messages": 15,
  "limit": 50
}

GET /api/messages/stats

Einfacher Statistikendpunkt.

Beispiel-Response

{
  "total_messages": 150,
  "total_users": 25,
  "most_active_user": {
    "username": "chat_lover",
    "message_count": 42
  },
  "messages_today": 15,
  "average_message_length": 45.7
}

4. WebSocket-Schnittstelle
Endpoint: /ws

Beispielverbindung im Browser:

const ws = new WebSocket('ws://localhost:8000/ws');

4.1 Nachrichtentypen
Chat-Nachricht senden
{
  "type": "chat_message",
  "username": "benutzer",
  "message": "Hallo Welt!",
  "timestamp": "2024-01-01T12:00:00Z"
}

Chat-Nachricht empfangen
{
  "type": "chat_message",
  "username": "benutzer",
  "message": "Hallo Welt!",
  "timestamp": "2024-01-01T12:00:00Z"
}

Benutzer beigetreten
{
  "type": "user_joined",
  "username": "neuer_benutzer",
  "timestamp": "2024-01-01T12:00:00Z"
}

Fehlernachricht
{
  "type": "error",
  "message": "Ungültige Nachricht",
  "timestamp": "2024-01-01T12:00:00Z"
}

5. Datenmodelle
Message
{
  "id": 1,
  "username": "Benutzer",
  "message": "Hallo Welt",
  "timestamp": "2024-01-01T12:00:00"
}

WebSocketMessage
{
  "type": "chat_message",
  "username": "Benutzer",
  "message": "Hallo Welt",
  "timestamp": "2024-01-01T12:00:00Z"
}

ErrorResponse
{
  "error": true,
  "message": "Fehlerbeschreibung",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}

6. Schnellstart
6.1 Health-Check
curl http://localhost:8000/health

6.2 Letzte Nachrichten abrufen
curl http://localhost:8000/api/messages/recent?limit=10

6.3 WebSocket-Test im Browser
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  console.log('Empfangen:', JSON.parse(event.data));
};

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'chat_message',
    username: 'test',
    message: 'Hallo WebSocket!'
  }));
};

7. Fehlercodes
Code	Bedeutung
400	Ungültige Anfrage
404	Ressource nicht gefunden
422	Validierungsfehler
500	Interner Serverfehler
8. Changelog
Version 1.0.0

Grundlegende Chatfunktion

WebSocket-Kommunikation

REST-API für Nachrichten

SQLite-Unterstützung