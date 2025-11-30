📘 README – EnvironmentSettings (Konfigurations- & Validierungsmodul)
Zweck der Datei

Diese Datei definiert eine zentrale Konfigurationsklasse für das System.
Sie dient dazu,

Umgebungsvariablen strukturiert einzulesen,

Werte automatisch zu validieren,

Abhängigkeiten zwischen Funktionen und Modulen zu prüfen,

sicherheitsrelevante Parameter zu kontrollieren,

optionale Funktionen je nach Konfiguration zu aktivieren oder zu deaktivieren.

Die Umsetzung basiert auf Pydantic v2 und pydantic-settings, wodurch typische Fehlerquellen wie falsche Datentypen oder ungültige URLs bereits beim Start erkannt werden.

Übersicht der Hauptfunktionen
Funktion	Beschreibung
Laden von Umgebungsvariablen	Werte aus .env oder dem System werden automatisch übernommen
Validierung aller Parameter	Typen, Wertebereiche, Sicherheitslimits, URLs, Ports usw.
Erkennen fehlerhafter Konfigurationen	Fehlende Schlüssel, ungültige Verzeichnisse, API-Konflikte
Feature-Flag-System	Kontrollierbare Aktivierung einzelner Systemfunktionen
Bereitstellung strukturierter Konfigurationsgruppen	z. B. AI, Sicherheit, Dateien, Caching, WebSockets
Erstellung sicherer Konfigurationsdarstellungen	Vermeidung des Ausgebens sensibler Daten
Modellkonfiguration

Die Pydantic-Modelleinstellungen sind wie folgt definiert:

.env als Standard-Konfigurationsquelle

automatische Typprüfung

automatische Verzeichnis-Erstellung bei Bedarf

extra="ignore" → unbekannte Variablen werden ignoriert

Dies ermöglicht eine kontrollierte, vorhersehbare und nachvollziehbare Initialisierung.

Struktur der Konfiguration

Das Modell gliedert die Einstellungen in folgende Bereiche:

1. Applikationskonfiguration

Name, Version, Debug-Status, Zeitzone

Secret Keys (mit Mindestlänge)

gültige Umgebungsstufen (development, production, staging, testing)

2. Serverkonfiguration

Host (IP-Validierung)

Ports (nur 1024–65535)

Worker-Anzahl (Konfliktvermeidung bei reload=True)

3. Datenbankkonfiguration

SQLite und PostgreSQL werden unterstützt

URL-Formatprüfung

Erstellen fehlender SQLite-Verzeichnisse

Pooling-Parameter für SQL-Backends

4. CORS-Konfiguration

Ursprünge können als Liste oder String angegeben werden

Validierung der Methoden, Header, Credentials

5. AI- und Modellkonfiguration

Ollama-URL-Validierung

Temperature, Top-P, Penalties

custom-model-Pfadprüfung

RAG-Einstellungen inkl. Pfadprüfung

6. Sicherheitsfunktionen

Rate-Limiting (verschiedene Strategien)

JWT-Einstellungen inklusive Sicherheitschecks

7. Feature Flags

Aktivierbar sind u. a.:

Projektmanagement

Ticket-System

Datei-Upload

Real-Time-Chat

Sentiment-Analyse

AI-Vorschläge

Moderation

Optional sind interne Prüfungen verfügbar, z. B. ob WebSockets für den Chat aktiviert sind.

8. Datei-Upload

Erstellen von Verzeichnissen

Prüfung erlaubter Dateiendungen

Maximalgrößen

9. Monitoring

Metriken

Health Checks

Performance-Monitoring

10. Caching

Memory / Redis

Redis-URL-Validierung

11. E-Mail

Prüfung vollständiger SMTP-Konfiguration wenn aktiviert

12. WebSockets

Maximalgrößen

Ping-Timeouts

Aktivierungsprüfung

13. Background Tasks

Worker-Anzahl

Retry-Versuche

Validierungsmethoden

Die Datei enthält umfangreiche Validierungen:

Feldvalidierungen (@field_validator)

HOST → IP-Formatprüfung

PORT → Bereichsprüfung

Secret Keys → Mindestlänge

DATABASE_URL → Format- und Pfadprüfung

CORS_ORIGINS → String- oder Listenformat

VECTOR_DB_TYPE → erlaubte Werte

Rate-Limit-Strategien → feste Begriffe

Upload-Ordner → automatische Verzeichniserstellung

Modellvalidierungen (@model_validator)

Konflikt Reload vs. Worker

Prüfung existierender Modellpfade

E-Mail-Konfigurationsprüfung

Redis-URL bei Redis-Cache

RAG-Pfaderstellung

Gruppierte Konfigurationen

Zur besseren Struktur enthält das Modell mehrere zusammengefasste Konfigurationsblöcke:

ai_config

security_config

file_config

feature_config

system_config

Diese liefern klare Datenstrukturen für andere Module.

Sichere Ausgabe sensibler Settings

Die Methode:

get_safe_settings()


liefert eine Darstellung, die folgende Daten ausblendet:

Secret Keys

Passwortfelder

vollständige Datenbank-URLs

Diese Informationen eignen sich für Log-Ausgaben oder Debugging ohne Sicherheitsrisiken.

Feature-Abhängigkeitsprüfung

Die Methode:

validate_feature_dependencies()


prüft, ob bestimmte Features zwingende Abhängigkeiten haben.
Beispiele:

Authentication ↔ JWT

Realtime Chat ↔ WebSockets

RAG ↔ AI

Ergebnisse werden als Warnungen ausgegeben und helfen beim Erkennen fehlerhafter Kombinationen.

Initialisierung und Fehlerverhalten

Beim Erzeugen der settings-Instanz:

werden alle Validierungen ausgeführt,

Fehler führen zu einer erklärenden Ausgabe,

abhängigkeitsbezogene Warnungen werden ausgegeben.

Das Verhalten ist präzise und verweist auf greifbare Probleme, z. B.:

ungültige URLs

fehlende Ordner

widersprüchliche Feature-Kombinationen

kurze Schlüssel

unvollständige E-Mail-Konfiguration

Beispiel: Zugriff im Projekt
from config.env_settings import settings

print(settings.APP_NAME)
print(settings.ai_config)
print(settings.security_config["rate_limiting"])


Konfigurationsgruppen lassen sich direkt in Services oder Routern nutzen.

Beispiel: Validierungswarnungen
warnings = settings.validate_feature_dependencies()
for w in warnings:
    print("- " + w)