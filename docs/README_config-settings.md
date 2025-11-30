📘 README – Logging- und Konfigurationsmodul
Übersicht

Dieses Modul stellt eine erweiterte Logging- und Konfigurationsinfrastruktur für das System bereit.
Der Fokus liegt auf:

einheitlicher Protokollierung

konfigurierbaren Ausgabeformaten

strukturierter Initialisierung

Validierung der Umgebungsparameter

systematischer Aufbereitung von System- und AI-Konfigurationen

erweiterbaren Log-Methoden (Performance, Sicherheit, Datenbankzugriffe)

Das Modul setzt auf Pydantic Settings, um Umgebungsvariablen zuverlässig zu laden und zu validieren.
Die Logging-Funktionen basieren auf dem Python-Modul logging.

Inhaltsverzeichnis

Dateien im Modul

Hauptbestandteile

EnvironmentSettings

setup_logging

EnhancedLogger

Konfigurationsvalidierung

Systeminformationen

Initialisierung beim Import

Integration im Projekt

Dateien im Modul
Datei	Zweck
validation.py	Enthält EnvironmentSettings (Pydantic-Konfiguration)
__init__.py	Macht die Hauptobjekte nach außen verfügbar
diese Datei	Initialisiert Logging, erzeugt EnhancedLogger, validiert die Umgebung
Hauptbestandteile

Das Modul besteht aus vier zentralen Bereichen:

EnvironmentSettings – Validierung und Laden der Konfiguration

setup_logging() – Initialisierung des Logging-Systems

EnhancedLogger – erweiterte Logger-Funktionalität

Konfigurationsdiagnose – Auswertung der Umgebungsparameter

EnvironmentSettings

Die Klasse EnvironmentSettings erweitert Pydantics BaseSettings.
Sie bietet:

Laden von .env oder Umgebungsvariablen

Typprüfung und Validierung

Warnungen für unsichere oder problematische Parameter

Strukturierte Zugriffsmethoden auf AI-, Sicherheits- und Serverkonfigurationen

Die Klasse validiert u. a.:

Ports

URLs

AI-Konfigurationen

CORS-Einstellungen

Rate-Limiting-Parameter

Log-Level

Jede Validierung verweist auf real nachvollziehbare Risiken (z. B. Debug-Modus, kurze Schlüssel, CORS-Wildcard).

setup_logging()

Diese Funktion richtet das Loggingsystem vollständig ein.
Sie wird automatisch beim Import ausgeführt.

Unterstützte Ausgabeformate
Format	Beschreibung
console	Farblich markierte, übersichtliche Konsolenausgabe (TTY-abhängig)
detailed	Erweitertes Format mit Modulen, Funktionen und Zeilennummern
json	JSON-Format für externe Log-Systeme (z. B. ELK, Loki, Splunk)
Funktionen

Erzeugt ein logs/-Verzeichnis

Rotation der Logdateien bis 10 MB

Setzt Warnlevel für externe Bibliotheken

Überschreibt existierende Handler, um doppelte Ausgaben zu verhindern

Gibt Statusmeldungen über Initialisierung aus

EnhancedLogger

Eine Wrapper-Klasse um logging.Logger mit zusätzlichen Methoden:

Methodenübersicht
Methode	Beschreibung
debug, info, warning, error, critical	Standard-Logging mit Zusatzfeldern
performance(operation, duration)	Protokollierung von Laufzeiten
security(event, user, ip)	Protokollierung sicherheitsrelevanter Ereignisse
database(operation, table, duration)	Logging von Datenbankaktivitäten

Alle Methoden erlauben zusätzliche strukturierte Felder, die ins Log eingebettet werden.

Konfigurationsvalidierung

Nach dem Laden erfolgt:

Prüfung der Umgebungsvariablen

Warnungen bei potenziellen Problemen

Sicherheits-Checks für Produktion

Prüfung von AI- und RAG-Einstellungen

Hinweise für fehlerhafte oder riskante Konfigurationen

Diese Validierung ist sachlich begründet und verweist auf real nachvollziehbare Probleme (z. B. CORS *, kurze Schlüssel, SQLite in Produktion).

Systeminformationen

Die Funktion get_system_info() erfasst:

Betriebssystem

Python-Version

CPU-Kernerkennung

Speicher

Disk-Auslastung

Prozess-ID

Falls Bibliotheken wie psutil fehlen, wird auf Basisinformationen zurückgegriffen.

Initialisierung beim Import

Beim Laden des Moduls wird automatisch:

Logging initialisiert

Die Konfiguration zusammengefasst

Die Umgebung validiert

Systeminformationen ausgegeben

Feature-Verfügbarkeit protokolliert

Die finale Meldung lautet:

„Application configuration completed successfully“

sofern keine kritischen Fehler auftreten.

Integration im Projekt
Verwendung des erweiterten Loggers
from config import enhanced_logger as log

log.info("Server started", port=8000)
log.performance("Database Query", duration=0.42)
log.security("Unauthorized access", user="guest", ip="127.0.0.1")

Zugriff auf Einstellungen
from config import settings

if settings.AI_ENABLED:
    model = settings.OLLAMA_DEFAULT_MODEL

Verwendung eigener Loggerinstanzen
from config.logging_module import EnhancedLogger

api_log = EnhancedLogger("api")
api_log.info("Request received", path="/messages")