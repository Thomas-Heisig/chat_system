README – Frontend-Client (index.html)
1. Zweck der Datei

Diese Datei bildet die vollständige Benutzeroberfläche für das Chat- und Kollaborationssystem.
Sie stellt die HTML-Grundstruktur bereit, die anschließend durch CSS und JavaScript dynamisch erweitert wird.
Die Datei enthält:

Navigationsbereich

Chatoberfläche

Räume

Benutzerlisten

AI-Assistent

Projekt- und Ticketmodule

Dateimanager

Analytikkomponenten

Verbindungsschnittstellen zum WebSocket-Backend

Die Logik wird über eine separate Datei (chat.js) gesteuert.

2. Gesamtaufbau

Die Seite ist in zwei Hauptbereiche unterteilt:

2.1 Sidebar (linke Spalte)

Der Sidebar-Bereich hält statische Navigation und dynamische Listen bereit:

Benutzerprofil (Avatar, Name, Status)

Hauptnavigation (Chat, Projekte, Tickets, Dateien, AI, Analytics)

Raumliste

Online-Benutzerliste

Systemstatus (AI-Status, Verbindungsstatus)

Er ergänzt die WebSocket-Daten des Backends über folgende Anzeigen:

aktive Räume

Anzahl der Teilnehmer pro Raum

Anzeige aller verbundenen Benutzer

Auf der Sidebar basieren sämtliche Wechsel zwischen den Hauptmodulen.

2.2 Hauptbereich (rechte Spalte)

Der Inhalt wird sektionsweise angezeigt:

Chat

Projektverwaltung

Ticketsystem

Dateimanager

AI-Assistent

Analytics

Jede Sektion wird über die Navigation ein- bzw. ausgeblendet.

3. Detaillierter Funktionsüberblick
3.1 Chatmodul
Bestandteile

Chatkopf mit Raumname, Metadaten und Einstellungen

Eingabe für Benutzername

Statistikfelder (Nachrichtenanzahl, Online-Zeit)

Nachrichtenlog mit System- und Benutzermeldungen

Eingabebereich für Nachrichten

Unterstützungsfunktionen:

Datei-Upload

Emoji-Auswahl

AI-Antwortoption

Textformatierungsbutton

Tippindikatoren

Raumbezogene Nachrichtenanzeige

Verbindungsintegration

Das Chatmodul reagiert auf folgende WebSocket-Ereignisse:

eingehende Chatnachrichten

Benutzer betritt Raum

Benutzer verlässt Raum

AI-Antworten

Systemmeldungen (Willkommenspaket, Historie)

Tipp-Indikatoren

Raumstatistiken

3.2 Projektmodul

Enthält:

Übersichtsgitter der vorhandenen Projekte

Button zum Erstellen eines neuen Projekts

Die eigentliche Logik erfolgt später durch JavaScript-API-Aufrufe.

3.3 Ticketsystem

Der Aufbau entspricht dem Projektmodul:

Ticketliste

Erstellen-Button

Auch hier erfolgt die Funktionalität über APIs und WebSocket-Nachrichten.

3.4 Dateimanager

Funktionen:

Anzeige von Dateien

Upload-Schaltfläche

Vorbereitung für Upload-Dialog über Modal

Integration mit file_upload_request aus dem Backend

3.5 AI-Assistent

Der Bereich enthält:

Ausgabe aller AI-Konversationselemente

Auswahl des Modells

Eingabefeld für Fragen

Auslösen einer AI-Anfrage über WebSocket

Der Bereich ist für ai_request Nachrichten ausgelegt.

3.6 Analytics

Diese Sektion zeigt:

Gesamtzahl Nachrichten

Anzahl aktiver Benutzer

Anzahl AI-Antworten

Anzahl Projekte

optional nutzbare Diagrammfläche

Daten werden durch regelmäßige WebSocket-Ereignisse und API-Abfragen aktualisiert.

4. Modals und Overlays
4.1 Profil-Einstellungen

Vorbereitet für spätere Benutzerkonfigurationen.

4.2 Raum erstellen

Popup zum Erstellen zusätzlicher Räume.
Anbindung über Nachrichtentyp room_join.

4.3 Dateiupload

In Kombination mit file_upload_request.
Das Modal steuert den Uploadfluss.

5. Systemmechanismen
5.1 Benachrichtigungssystem

Container für systemweite Hinweise.
Steuerung über JavaScript.

5.2 Laden-Spinner

Zur Anzeige während Netzwerkoperationen.

5.3 Verbindungsleiste (Connection Bar)

Wird genutzt für:

Verbindungsstatus

Ping-Messungen

Nachrichtentransferrate

Die Werte stammen direkt aus den WebSocket-Events.

6. Interaktion mit chat.js

Das HTML ist darauf ausgerichtet, dass chat.js folgende Aufgaben übernimmt:

Aufbau und Verwaltung der WebSocket-Verbindung

Aktualisierung der Benutzeroberfläche

Wechsel der Sektionen

Chatnachrichten erzeugen, senden und empfangen

Räume anlegen, betreten, wechseln

Benutzerstatus aktualisieren

File-Upload initiieren

AI-Anfragen senden und Antworten anzeigen

Statistiken auswerten

Ereignisse protokollieren

Die HTML-Elemente sind entsprechend über IDs markiert.

7. Barrierefreiheit

Die Datei enthält:

aria-* Attribute

klare Beschriftungen

Rollen (role="log", role="status", ...)

Dies soll die Bedienung mit Screen-Readern ermöglichen.

8. Strukturaufteilung in Bereichen

Die HTML-Datei lässt sich in fünf Segmente gliedern:

Bereich	Zweck
<head>	Metadaten, CSS, Scripts
<aside>	Navigation, Räume, Benutzer, Systemstatus
<main>	Funktionsmodule
Modals	Overlays für Eingaben
Systemelemente	Benachrichtigungen, Ladeindikatoren, Verbindungsbar

Diese Struktur formt die Grundlage für ein modular gesteuertes Echtzeit-Frontend.

9. Zusammenfassung

Das HTML-Dokument bildet die visuelle Oberfläche des Systems und stellt sämtliche UI-Elemente für folgende Funktionen bereit:

Echtzeit-Chat

Raumverwaltung

Benutzerverwaltung

Projektmanagement

Ticketsystem

Dateiverwaltung

AI-Kommunikation

Analyseanzeigen

Alle dynamischen Aspekte werden über chat.js und die WebSocket-Schnittstelle implementiert.