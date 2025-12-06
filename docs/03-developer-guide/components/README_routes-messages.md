📘 README – Messages API Router
Zweck der Datei

Diese Datei stellt alle HTTP-Routen für Nachrichten bereit. Sie ergänzt die globale Routing-Schicht des Systems um sämtliche Funktionen zur Nachrichtenverwaltung, Statistik, Suche und AI-Analyse.
Sie bindet außerdem die relevanten Services und Datenbank-Repositories ein.

Der Router deckt folgende Bereiche ab:

Nachrichten abfragen

Nachrichten nach Usern, Projekten, Räumen und Typen filtern

Reaktionen hinzufügen und auslesen

Kontext einer Nachricht abrufen

Statistische Auswertungen

Semantic- und Keyword-Suche

Exportfunktionen

Bereinigung alter Daten

Architektur

Die Datei nutzt folgende Komponenten:

Service-Schicht

MessageService: Geschäftslogik rund um Nachrichten und AI-Operationen.

Repository-Schicht

MessageRepository

UserRepository

ProjectRepository

TicketRepository

StatisticsRepository

Diese kapseln alle direkten Datenbankzugriffe.

Modelle

Message, MessageFilter, MessageType

PaginatedResponse

MessageBatch

Hilfsfunktionen (create_message, create_ai_message)

Initialisierung

Beim Import werden:

alle Repositories erzeugt

die Services instanziert

Fehler vollständig protokolliert

Dies erlaubt dem gesamten Router, ohne erneut Instanzen zu erzeugen, auf dieselben Objekte zurückzugreifen.

1. Basis-Nachrichten-Endpunkte
GET /messages

Liefert paginierte Nachrichten

Unterstützt Filter:

Benutzer

Nachrichtentyp

Raum

Projekt

Ticket

Alle Filter werden in ein MessageFilter-Objekt überführt.

GET /messages/recent

Liefert die neuesten Nachrichten

Optional eingeschränkt nach:

Raum

Projekt

Führt einfache Statistikauswertung für Logging durch:

Anzahl beteiligter Benutzer

Anzahl AI-Antworten

GET /messages/user/{username}

Liefert alle Nachrichten eines bestimmten Benutzers

Optional gefiltert nach Projekt

Paginierbar

2. Erweiterte Nachrichten-Endpunkte
GET /messages/{id}

Holt eine Nachricht inkl.:

komplette Datenstruktur

Reaktionen

Reaktionsanzahl

GET /messages/{id}/context

Liefert Nachrichten um die Zielnachricht herum

Größe des Kontextfensters ist konfigurierbar

Kernfunktion für KI-Kontextbildung

POST /messages/{id}/reactions

Fügt einer Nachricht eine Reaktion hinzu

Nutzt Repository-Methode zum Eintragen der Reaktion

GET /messages/{id}/reactions

Gibt alle Reaktionen auf diese Nachricht zurück

Erzeugt zusätzlich eine aggregierte Statistik nach Reaktionstyp

3. Statistik- und Analyse-Endpunkte
GET /messages/stats

Ermittelt Statistiken über Nachrichten, u. a.:

Gesamtnachrichten

Nutzeranzahl

aktivster Nutzer

Verteilung der Nachrichtentypen

AI-Antworten inkl. Modellverteilung

Zeitspanne vom ersten bis zum letzten Eintrag

Filterbar nach:

Zeitfenster (Tag, Woche, Monat, Jahr)

Projekt

Die Berechnung läuft vollständig im Service, ohne SQL-Aggregation.

GET /messages/count

Liefert nur die Gesamtanzahl der Nachrichten

Optional gefiltert nach:

Projekt

Raum

GET /messages/ai/stats

Auswertung von AI-Interaktionen

Beruht auf repository-basierter Statistikfunktion

4. Such-Endpunkte
GET /messages/search

Zwei Suchmodi:

semantic (KI-gestützt; abhängig vom Repository)

keyword (klassische LIKE-Filter)

Exportiert:

Ergebnisse als Liste

Suchtyp

Zeitstempel

5. Projektbezogene Nachrichten
GET /messages/project/{project_id}

Liefert Nachrichten eines Projekts

Enthält:

Nachrichten

Pagination

Projektinformationen (optional)

6. Wartung & Export
DELETE /messages/cleanup

Löscht Nachrichten, die älter als X Tage sind

Optional kann man KI-Nachrichten behalten

Typischer Admin-Endpunkt

GET /messages/export

Exportiert Nachrichten:

JSON: alle vollständigen Datensätze

CSV: aktuell nur strukturiertes Export-Objekt, keine Datei

Unterstützt optional:

Startdatum

Enddatum

Fazit

Dieser Router bildet die komplette API-Schicht für Nachrichtenfunktionen, inkl.:

Verwaltung

Kontext

Suche

Reaktionen

Statistiken

projekt- und raumbasierte Filter

Exporte

Datenbereinigung

Er ist vollständig modularisiert, nutzt zentrale Repositories und bietet umfassende Logging-Informationen für Diagnose und Fehlersuche.