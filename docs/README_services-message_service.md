README – MessageService
1. Zweck der Klasse

Der MessageService ist die zentrale Fachlogik für:

Speichern von Nachrichten

Auslesen verschiedener Nachrichtentypen

Erzeugen von AI-Antworten (Optional, abhängig von Systemverfügbarkeit)

Validierung der Eingaben

Zusammenführen von Benutzer-Nachrichten und AI-generierten Antworten

Durchführung einfacher Analysen wie Sentiment-Bewertung

Bereitstellen eines technischen Health-Checks

Der Service ist unabhängig vom Webframework aufgebaut und nutzt ausschließlich das MessageRepository als Persistenzschicht.

2. Abhängigkeiten
Repositories

MessageRepository (Kern der Datenhaltung)

Modelle

Message

MessageType

Weitere importierte Hilfsmodule für Filter und Strukturierung

Externe Dienste

Ollama (lokale AI-Modelle, geprüft über /api/tags)

Optionaler Custom-Model-Pfad (über Umgebungsvariable)

Systembibliotheken

requests für API-Calls

os, json, datetime

Logging (logger, enhanced_logger)

3. Initialisierung

Beim Erstellen der Instanz führt der Service folgende Prüfungen durch:

Erreichbarkeit von Ollama

Existenz eines optionalen Custom Models

Setzen interner Zustände:

ollama_available

custom_model_available

Alle Ergebnisse werden protokolliert.

4. AI-Model-Management
4.1 Modellverfügbarkeit
get_available_models()


Liefert eine Liste verfügbarer Modelle:

Modelle aus Ollama (abgefragt über /api/tags)

Simulierter Eintrag für ein Custom-Modell, falls vorhanden

4.2 Modellprüfung

Verfügbarkeit wird ausschließlich über HTTP und Dateipfade geprüft

Keine inhaltliche Validierung der Modelle

5. AI-Antwortgenerierung
5.1 Zentrale Funktion
generate_ai_response(message, context_messages, model_type, model_name)


Ablauf:

Kontext der letzten Nachrichten wird zusammengeführt

Modell wird abhängig von Systemzustand gewählt:

bevorzugt Ollama

falls nicht verfügbar → Custom-Modell

falls beide nicht verfügbar → Fallback-Antwort

5.2 Unterstützung der Modelltypen
Modelltyp	Methode	Beschreibung
ollama	_generate_with_ollama()	Anfrage an lokalen HTTP-Server
custom	_generate_with_custom_model()	Logik ausschließlich simuliert
none	_generate_fallback_response()	Antwort ohne AI
5.3 Prompt-Generierung
_build_prompt()


Erstellt ein einfaches Prompt mit optionalem Gesprächskontext.

6. Zentrale Fachfunktionen
6.1 Nachricht speichern
save_message(message)


Validiert Benutzername und Nachrichtentext

Übergibt das Modell an das Repository

Setzt die generierte ID wieder in das Modell zurück

6.2 Nachricht + AI-Antwort speichern
save_message_with_ai_response(message, use_ai=True)


Ablauf:

Benutzer-Nachricht speichern

Optional Kontext laden

AI-Antwort erzeugen

AI-Nachricht speichern

Ergebnis als strukturierte Antwort zurückgeben

6.3 Fragen an AI
ask_question(question, username, use_context, model_type, project_id)


Speichert:

Die Frage

Die AI-Antwort

Optional den Kontext

7. Analysefunktionen
7.1 Sentimentanalyse
analyze_message_sentiment(message)


Bei aktiver AI wird ein JSON-Prompt an Ollama gesendet

Bei Fehler oder Nichtverfügbarkeit erfolgt eine rein lokale Basisauswertung

Rückgabe ist immer ein strukturiertes Dictionary

8. Abrufmethoden
8.1 get_recent_messages(limit)

Limit wird geprüft und ggf. begrenzt

Der Repository-Call wird protokolliert

8.2 get_all_messages()

Vollständiges Laden aller Nachrichten aus der Persistenz.

8.3 get_user_messages(username, limit)

Filtert Nachrichten anhand des Benutzernamens aus dem Gesamtdatensatz.

9. Dienstinformationen
9.1 AI-Status
get_ai_status()


Liefert strukturiert:

AI aktiviert/ deaktiviert

Welche Modelle verfügbar sind

Status von Ollama

Pfad der Custom-Modelle

Zeitstempel

9.2 Health-Check
health_check()


Prüft Lesen der Nachrichten

Fragt den AI-Status ab

Meldet Repository-Verbindung

Rückgabe: "healthy" oder "unhealthy"

10. Beobachtungen zur Architektur
Volle Funktionsfähigkeit:

Speichern und Laden von Nachrichten

AI-Antwortgenerierung über Ollama

fallback-basierte Custom-Modell-Logik

Eingabevalidierung und Fehlerprotokollierung

Punkte mit Einschränkungen:

Custom-Modell ist nur simuliert

Sentimentanalyse hängt stark vom Ollama-Modell ab

get_user_messages lädt immer den gesamten Datenbestand

Kontextverarbeitung beschränkt sich auf den Text, keine Rollenlogik

Fehlerbehandlung ist funktional, aber teilweise grob (keine differenzierten Statuscodes)

11. Zusammenfassung

Der MessageService implementiert eine vollständige Nachrichtenverwaltung mit integrierter AI-Verarbeitung.
Er ist klar strukturiert, modular aufgebaut und technisch nachvollziehbar.
Die AI-Logik bleibt bewusst einfach gehalten, ist aber erweiterbar.
Fehlerbehandlung und Logging sind integraler Bestandteil jeder Methode.