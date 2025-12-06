README – ConnectionManager (WebSocket-Verwaltung)
1. Zweck der Datei

Der ConnectionManager übernimmt die zentrale Verwaltung aller WebSocket-Verbindungen.
Er abstrahiert den kompletten Lifecycle einer Verbindung und ergänzt den Chat-Server um Raum-, Benutzer-, Sicherheits- und Monitoring-Funktionalitäten.

Der Code dient als Infrastrukturkomponente und ist unabhängig von Chat-Logik oder AI-Services.

2. Hauptaufgaben des ConnectionManagers

Der Manager erfüllt mehrere technische Aufgaben:

2.1 Verbindungsverwaltung

Annehmen neuer WebSocket-Verbindungen

Generieren eindeutiger Verbindungs-IDs

Führen einer Liste aktiver Verbindungen

Entfernen und Bereinigen abgebrochener Verbindungen

2.2 Benutzerverwaltung

Verknüpfen einer WebSocket-Verbindung mit einem Benutzernamen

Verwaltung mehrerer paralleler Verbindungen pro Benutzer

Entfernen, wenn Benutzer getrennt werden

2.3 Raumverwaltung (Rooms)

Erstellen und Verwalten virtueller Räume

Beitritt und Austritt von Räumen

Ermitteln aller Verbindungen in einem Raum

2.4 Nachrichtenversand

Der Manager stellt zwei Versandmechanismen bereit:

Direktversand (send_personal_message)

Nachricht geht gezielt an eine einzelne WebSocket-Verbindung

Broadcast (broadcast)

Versand an alle aktiven Verbindungen oder gezielt an Raum-Mitglieder

Fehler werden erfasst und Verbindungen bereinigt

2.5 Überwachung / Monitoring

Es werden interne Statistiken gesammelt:

Anzahl aktiver Verbindungen

Peak-Verbindungen

Nachrichtenanzahl pro Typ

Fehleranzahl

Raumanzahl

Aktivitätszeitpunkt pro Verbindung

Diese Werte können über get_connection_stats() ausgelesen werden.

2.6 Sicherheits- und Stabilitätsfunktionen

Ping-Nachrichten zur Prüfung der Verbindung

Cleanup inaktiver Verbindungen

Verhindern des Sendens an ungültige WebSockets

Getrennte Statistik für Fehlerfälle

3. Datenstrukturen
3.1 ConnectionState

Beschreibt den Zustand einer WebSocket-Verbindung:

Zustand	Bedeutung
CONNECTED	Verbindung besteht, aber nicht authentifiziert
AUTHENTICATED	Benutzer erfolgreich angemeldet
DISCONNECTED	Verbindung geschlossen
INACTIVE	Verbindung wurde wegen Inaktivität entfernt
3.2 ConnectionType

Beschreibt die Art der Verbindung:

Typ	Bedeutung
USER	Standard-Verbindung eines Nutzers
AI_ASSISTANT	Verbindung eines KI-Moduls
SYSTEM	interne Systemverbindungen
GUEST	nicht authentifizierte Verbindung
4. Interne Verwaltungsspeicher

Der Manager speichert Daten in mehreren internen Strukturen:

4.1 active_connections: List[WebSocket]

Liste aller offenen Verbindungen.

4.2 connection_info: Dict[WebSocket, Dict]

Per-Verbindung-Metadaten:

ID

Zeitpunkte

Benutzername

Nachrichtenanzahl

Räume

IP-Adresse

4.3 user_connections: Dict[str, Set[WebSocket]]

Ordnet Benutzername → alle Verbindungen des Benutzers.

4.4 room_connections: Dict[str, Set[WebSocket]]

Ordnet Raum-ID → Verbindungen im Raum.

5. Zentrale Funktionen
5.1 connect()

akzeptiert die Verbindung

erzeugt Verbindungseintrag

erstellt eindeutige ID

aktualisiert Statistiken

5.2 disconnect()

entfernt Benutzer aus Räumen

entfernt Verbindung

entfernt Benutzerzuordnung

Protokolliert alle relevanten Daten

5.3 authenticate_user()

ordnet WebSocket einem Benutzer zu

aktualisiert user_connections

5.4 join_room() / leave_room()

setzt die Raumzuordnung

aktualisiert Raumstatistiken

5.5 send_personal_message()

fügt Metadaten hinzu

sendet Nachricht

aktualisiert Statistiken

5.6 broadcast()

Versand an Raum oder alle Verbindungen

parallele Ausführung über asyncio.gather

Fehlerbehandlung und Disconnects

6. Wartungs- und Diagnosefunktionen
6.1 cleanup_inactive_connections()

Entfernt Verbindungen ohne Aktivität über einem Grenzwert.

6.2 send_ping()

Übermittelt "Ping"-Nachricht zur Verbindungsprüfung.

6.3 get_connection_stats()

Gibt vollständige aktuelle Systemstatistik zurück:

aktive Verbindungen

Nutzeranzahl

Raumanzahl

Nachrichtenstatistik

Performance-Metriken

6.4 get_room_stats(room_id)

Gibt Daten eines Raumes zurück:

Benutzerliste

Verbindungsanzahl

Aktivierungszeitpunkt

7. Designüberlegungen

Der Code nutzt einen bewusst modularen Ansatz:

Trennung zwischen WebSocket-Handling und Anwendungslogik
-> Erhöht Testbarkeit und Stabilität.

Einsatz von Sets für Benutzer- und Raumzuordnung
-> O(1)-Zugriff für Zuordnungen.

Konsequente Benutzung von UUIDs
-> Reduzieren Kollisionen, erleichtern Debugging.

Detailreiche Logging-Ausgaben
-> Erleichtert Fehlersuche und Monitoring.

Asynchrone Verteilung von Broadcasts
-> Belastung bleibt kontrolliert, skalierbarkeit besser.

8. Zusammenfassung

Der ConnectionManager implementiert:

vollständiges Management aller WebSocket-Verbindungen

Benutzer- und Raumverwaltung

Nachrichtenzustellung inkl. Fehlerhandling

Ping/Timeout-Mechanismen

transparente Statistiksammlung

erweiterte Diagnosefunktionen

Er bildet damit die Grundlage für Echtzeitkommunikation, ohne selbst fachliche Chatlogik zu implementieren.