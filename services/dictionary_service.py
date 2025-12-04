# services/dictionary_service.py
"""
📖 Dictionary System
Manages terminology and glossary functionality.

This is a placeholder for the planned dictionary system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import logger


class DictionaryService:
    """
    Wörterbuch-/Glossar-System

    Geplante Features:
    - Begriffsverwaltung mit Definitionen
    - Kategorisierung von Begriffen
    - Auto-Vervollständigung
    - Synonyme und verwandte Begriffe
    - Multi-Sprach-Unterstützung
    """

    def __init__(self):
        self.terms: Dict[str, Dict] = {}
        self.categories: Dict[str, List[str]] = {}
        self.synonyms: Dict[str, List[str]] = {}
        logger.info("📖 Dictionary Service initialized (placeholder)")

    async def add_term(
        self,
        term: str,
        definition: str,
        category: Optional[str] = None,
        examples: Optional[List[str]] = None,
        synonyms: Optional[List[str]] = None,
        related_terms: Optional[List[str]] = None,
        language: str = "de",
    ) -> Dict[str, Any]:
        """
        Fügt neuen Begriff hinzu

        Args:
            term: Begriff
            definition: Definition
            category: Optionale Kategorie
            examples: Optionale Beispiele
            synonyms: Optionale Synonyme
            related_terms: Optionale verwandte Begriffe
            language: Sprache (default: de)

        Returns:
            Dict mit Begriff-Informationen
        """
        term_id = f"term_{term.lower().replace(' ', '_')}_{datetime.now().timestamp()}"
        term_lower = term.lower()

        term_entry = {
            "id": term_id,
            "term": term,
            "term_lower": term_lower,
            "definition": definition,
            "category": category,
            "examples": examples or [],
            "synonyms": synonyms or [],
            "related_terms": related_terms or [],
            "language": language,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "created",
            "message": "Dictionary Service not yet implemented - term stored in memory only",
        }

        self.terms[term_id] = term_entry

        # Index by category
        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(term_id)

        # Index synonyms
        if synonyms:
            for synonym in synonyms:
                if synonym.lower() not in self.synonyms:
                    self.synonyms[synonym.lower()] = []
                self.synonyms[synonym.lower()].append(term_id)

        return term_entry

    async def lookup(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Sucht Begriff nach

        Args:
            term: Suchbegriff

        Returns:
            Dict mit Begriff oder None
        """
        term_lower = term.lower()

        # Direct lookup
        for entry in self.terms.values():
            if entry.get("term_lower") == term_lower:
                return entry

        # Synonym lookup
        if term_lower in self.synonyms:
            term_ids = self.synonyms[term_lower]
            if term_ids:
                return self.terms.get(term_ids[0])

        return None

    async def suggest(self, partial_term: str, limit: int = 10) -> List[str]:
        """
        Auto-Vervollständigung für Begriffe

        Args:
            partial_term: Teilbegriff
            limit: Maximale Vorschläge

        Returns:
            Liste mit Vorschlägen
        """
        suggestions = []
        partial_lower = partial_term.lower()

        for entry in self.terms.values():
            term = entry.get("term", "")
            if term.lower().startswith(partial_lower):
                suggestions.append(term)
                if len(suggestions) >= limit:
                    break

        # Also check synonyms
        for synonym in self.synonyms.keys():
            if synonym.startswith(partial_lower) and synonym not in suggestions:
                suggestions.append(synonym)
                if len(suggestions) >= limit:
                    break

        return suggestions[:limit]

    async def update_term(self, term_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert einen Begriff"""
        if term_id not in self.terms:
            return {"error": "Term not found", "term_id": term_id}

        entry = self.terms[term_id]

        for key, value in updates.items():
            if key in entry and key not in ["id", "created_at"]:
                entry[key] = value

        entry["updated_at"] = datetime.now().isoformat()
        return entry

    async def delete_term(self, term_id: str) -> bool:
        """Löscht einen Begriff"""
        if term_id in self.terms:
            del self.terms[term_id]
            return True
        return False

    async def get_terms_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Gibt alle Begriffe einer Kategorie zurück"""
        if category not in self.categories:
            return []

        term_ids = self.categories[category][:limit]
        return [self.terms[tid] for tid in term_ids if tid in self.terms]

    async def search_terms(
        self,
        query: str,
        category: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Durchsucht Begriffe

        Args:
            query: Suchbegriff
            category: Optional nach Kategorie filtern
            language: Optional nach Sprache filtern
            limit: Maximale Ergebnisse

        Returns:
            Liste mit passenden Begriffen
        """
        results = []
        query_lower = query.lower()

        for entry in self.terms.values():
            # Check if query matches term or definition
            if (
                query_lower in entry.get("term", "").lower()
                or query_lower in entry.get("definition", "").lower()
            ):

                # Filter by category
                if category and entry.get("category") != category:
                    continue

                # Filter by language
                if language and entry.get("language") != language:
                    continue

                results.append(entry)

                if len(results) >= limit:
                    break

        return results

    async def get_related_terms(self, term_id: str) -> List[Dict[str, Any]]:
        """Gibt verwandte Begriffe zurück"""
        if term_id not in self.terms:
            return []

        entry = self.terms[term_id]
        related_ids = entry.get("related_terms", [])

        results = []
        for related in related_ids:
            # Try to find by ID or term name
            if related in self.terms:
                results.append(self.terms[related])
            else:
                # Search by term name
                found = await self.lookup(related)
                if found:
                    results.append(found)

        return results

    async def get_all_categories(self) -> List[str]:
        """Gibt alle Kategorien zurück"""
        return list(self.categories.keys())

    async def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über das Wörterbuch zurück"""
        return {
            "total_terms": len(self.terms),
            "total_categories": len(self.categories),
            "total_synonyms": len(self.synonyms),
            "terms_by_category": {cat: len(terms) for cat, terms in self.categories.items()},
            "timestamp": datetime.now().isoformat(),
        }


# Singleton instance
_dictionary_service: Optional[DictionaryService] = None


def get_dictionary_service() -> DictionaryService:
    """Get or create the Dictionary service singleton"""
    global _dictionary_service
    if _dictionary_service is None:
        _dictionary_service = DictionaryService()
    return _dictionary_service
