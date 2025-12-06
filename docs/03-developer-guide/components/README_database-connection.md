📘 README – Datenbankmodul (SQLite, Verbindungen, Struktur, Wartung)
Übersicht

Dieses Modul implementiert eine strukturierte und erweiterbare Datenbankarchitektur auf Basis von SQLite.
Es stellt sowohl technische Basisfunktionen als auch komplexe Hilfsfunktionen bereit, die in größeren Backend-Systemen sinnvoll sind:

Verwaltung von Verbindungen pro Thread

Konfigurierbares WAL-Journal

performante Lese- und Schreibvorgänge

strukturierte Initialisierung aller Tabellen

Backup- und Restore-Mechanismen

Health-Check- und Diagnosefunktionen

regelmäßige Wartung zur Reduktion von Fragmentierung

einfache Migrationsunterstützung

optionale Kompression großer Textinhalte

Die Datei fungiert als Kernkomponente für sämtliche Repositories.

Inhaltsverzeichnis

Zweck des Moduls

Verbindungs- und Transaktionsverwaltung

Initialisierung der Datenbank

Tabellenübersicht

Backup und Wiederherstellung

Statistiken und Optimierung

Wartungsaufgaben

Health-Checks

Export und Migration

Kompression

Integration

Zweck des Moduls

Die Datei dient als zentrale Schnittstelle zur SQLite-Datenbank und deckt folgende Bereiche ab:

Bereitstellung einer standardisierten Verbindung

Optimierung der Zugriffe für Mehrthread-Umgebungen

Erstellung aller benötigten Tabellen

Gewährleistung konsistenter Daten durch Transaktionen

Unterstützung der Repositories mit einer stabilen Grundlage

Erstellung regelmäßiger Backups

Analyse der Datenbank- und Systemzustände

Die Implementierung berücksichtigt typische Engpässe bei SQLite (z. B. Locking, Journal-Mode, Transaktionsdauer) und setzt etablierte Strategien ein.

Verbindungs- und Transaktionsverwaltung
get_db_connection()

Ein Context Manager, der:

pro Thread eine wiederverwendbare Verbindung bereitstellt

read-only und read-write trennt

mit PRAGMA-Werten Performance und Stabilität verbessert

Write-Verbindungen im Thread-Kontext hält

Verbindungen validiert

sauber commit/rollback ausführt

Wichtige Einstellungen:

PRAGMA	Zweck
WAL	parallele Lesezugriffe
synchronous=NORMAL	reduziert IO-Kosten
cache_size	In-Memory-Caching
mmap_size	Memory-Mapping größerer Dateien
transaction()

Ein expliziter Transaktionsmanager für komplexere Skripte.

Initialisierung der Datenbank
init_database()

Erstellt alle Tabellen, Indizes und Standardwerte.

Der Ablauf:

Aktivieren der Erweiterungen

Erstellen der Tabellen

Einfügen von Standard-AI-Modellen (falls leer)

Anlegen eines Standard-Admin-Benutzers (falls keine Nutzer existieren)

Erstellen aller Indizes

Validierung über _verify_database_setup()

Tabellenübersicht

Die Datei legt eine Vielzahl von Tabellen an. Einige Kernpunkte:

messages

speichert Chatnachrichten

unterstützt Kompression großer Inhalte

unterstützt Threads, Räume, Metadaten

enthält Edit-Historie

users

Grundgerüst für Rollen, Verifizierung, Aktivität

kann später mit JWT-System verknüpft werden

projects / tickets

Basissystem für Projekt- und Ticketverwaltung

Foreign-Key-Beziehungen definieren Aufräumregeln

files

Informationen zu hochgeladenen Dateien

speichert Hashwerte für Erkennung von Duplikaten

chat_rooms / room_members

Chatraum- und Channel-Struktur

ai_models / ai_conversations

Backend für Modellverwaltung und Gesprächskontexte

audit_log

rudimentäres Sicherheits-/Revisionssystem

Alle Tabellen werden nach Erstellung über Indizes ergänzt, um Suchvorgänge messbar zu beschleunigen.

Backup und Wiederherstellung
backup_database()

Funktionen:

erstellt konsistente Backups über SQLite-Backup-API

optional komprimiert (gzip)

legt Backups in ./backups ab

schreibt Log-Einträge über Erfolgs- oder Fehlstatus

restore_database()

schließt bestehende Verbindungen

entpackt .gz-Backups

ersetzt aktive Datenbank durch Sicherung

meldet Erfolg oder Fehler in den Logs

Statistiken und Optimierung
get_database_stats()

Ermittelt umfassende Kennzahlen:

Anzahl der Datensätze pro Tabelle

Datenbankgröße

Page-Count, Freelist-Count

Aktivität in den letzten 1h, 24h, 7 Tagen

Speicherverbrauch einzelner Tabellen

schreibt strukturierte Logeinträge

optimize_database()

Zwei Betriebsmodi:

Modus	Maßnahmen
Standard	optimize, incremental_vacuum, analyze
Aggressiv	VACUUM, WAL-Checkpoint, Memory-Cleanup

VACUUM benötigt freie Dateisystem-Kapazität und dauert proportional zur DB-Größe.

Wartungsaufgaben
run_database_maintenance()

Führt automatische Aufgaben aus:

Löscht Audit-Logs älter als 90 Tage

Entfernt verwaiste temporäre Dateien

Führt Optimierungen aus

Erstellt ein Backup

schreibt detaillierte Logeinträge

Health-Checks
check_database_health()

Ermittelt:

grundlegende Erreichbarkeit

Integritätsstatus über PRAGMA integrity_check

Fremdschlüssel-Konsistenz

Journal-Mode

Anzahl laufender Transaktionen

Das Ergebnis wird klassifiziert in:

healthy

degraded

unhealthy

ausgehend von objektiven Kriterien.

Export und Migration
export_database_schema()

exportiert das gesamte Schema als .sql

ignoriert SQLite-interne Tabellen

ermöglicht Wiederaufbau der Struktur ohne Daten

get_database_version() / set_database_version()

nutzt PRAGMA user_version

erlaubt einfache Migrationsschritte

Kompression

Für große Nachrichten:

compress_text() verwendet zlib

should_compress() berechnet anhand Schwellwert

decompress_text() stellt Inhalte wieder her

Dies reduziert den benötigten Speicherplatz bei langen Texten.

Integration

Typische Verwendung aus einem Repository:

from database.core import get_db_connection

with get_db_connection() as conn:
    cursor = conn.execute("SELECT * FROM messages LIMIT 10")
    rows = cursor.fetchall()


Initialisierung beim Start des Backends:

from database.core import init_database

init_database()


Regelmäßige Wartung (z. B. Cron-Job):

from database.core import run_database_maintenance

run_database_maintenance()
