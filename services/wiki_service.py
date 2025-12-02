# services/wiki_service.py
"""
📚 Wiki System
Manages documentation and knowledge management.

This is a placeholder for the planned wiki system.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from config.settings import logger


class WikiService:
    """
    Wiki-System für Dokumentation und Wissensmanagement
    
    Geplante Features:
    - Wiki-Seiten Erstellung und Bearbeitung
    - Versionshistorie und Rollback
    - Volltextsuche
    - Kategorisierung und Tagging
    - Markdown-Unterstützung
    """
    
    def __init__(self):
        self.pages: Dict[str, Dict] = {}
        self.page_versions: Dict[str, List[Dict]] = {}
        logger.info("📚 Wiki Service initialized (placeholder)")
    
    async def create_page(
        self, 
        title: str, 
        content: str, 
        author: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Erstellt neue Wiki-Seite
        
        Args:
            title: Seitentitel
            content: Seiteninhalt (Markdown)
            author: Autor-ID
            category: Optionale Kategorie
            tags: Optionale Tags
            
        Returns:
            Dict mit Seiten-Informationen
        """
        page_id = f"wiki_{datetime.now().timestamp()}"
        
        page = {
            "id": page_id,
            "title": title,
            "content": content,
            "author": author,
            "category": category,
            "tags": tags or [],
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "created",
            "message": "Wiki Service not yet implemented - page stored in memory only"
        }
        
        self.pages[page_id] = page
        return page
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Gibt eine Wiki-Seite zurück"""
        return self.pages.get(page_id)
    
    async def get_page_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Sucht eine Seite nach Titel"""
        for page in self.pages.values():
            if page.get("title", "").lower() == title.lower():
                return page
        return None
    
    async def update_page(
        self, 
        page_id: str, 
        content: str, 
        editor: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aktualisiert Wiki-Seite mit Versionshistorie
        
        Args:
            page_id: Seiten-ID
            content: Neuer Inhalt
            editor: Editor-ID
            comment: Optionaler Kommentar zur Änderung
            
        Returns:
            Dict mit aktualisierten Seiten-Informationen
        """
        if page_id not in self.pages:
            return {
                "error": "Page not found",
                "page_id": page_id
            }
        
        page = self.pages[page_id]
        
        # Store version history
        if page_id not in self.page_versions:
            self.page_versions[page_id] = []
        
        self.page_versions[page_id].append({
            "version": page["version"],
            "content": page["content"],
            "editor": page.get("last_editor", page["author"]),
            "timestamp": page["updated_at"],
            "comment": comment
        })
        
        # Update page
        page["content"] = content
        page["version"] += 1
        page["last_editor"] = editor
        page["updated_at"] = datetime.now().isoformat()
        
        return page
    
    async def delete_page(self, page_id: str) -> bool:
        """Löscht eine Wiki-Seite"""
        if page_id in self.pages:
            del self.pages[page_id]
            return True
        return False
    
    async def get_page_history(self, page_id: str) -> List[Dict[str, Any]]:
        """Gibt die Versionshistorie einer Seite zurück"""
        return self.page_versions.get(page_id, [])
    
    async def restore_version(
        self, 
        page_id: str, 
        version: int,
        editor: str
    ) -> Dict[str, Any]:
        """Stellt eine frühere Version wieder her"""
        if page_id not in self.page_versions:
            return {"error": "No version history found"}
        
        for version_entry in self.page_versions[page_id]:
            if version_entry["version"] == version:
                return await self.update_page(
                    page_id, 
                    version_entry["content"], 
                    editor,
                    f"Restored from version {version}"
                )
        
        return {"error": f"Version {version} not found"}
    
    async def search(
        self, 
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Durchsucht Wiki-Seiten
        
        Args:
            query: Suchbegriff
            category: Optional nach Kategorie filtern
            tags: Optional nach Tags filtern
            limit: Maximale Ergebnisse
            
        Returns:
            Liste mit passenden Seiten
        """
        results = []
        query_lower = query.lower()
        
        for page in self.pages.values():
            # Check if query matches title or content
            if (query_lower in page.get("title", "").lower() or 
                query_lower in page.get("content", "").lower()):
                
                # Filter by category if specified
                if category and page.get("category") != category:
                    continue
                
                # Filter by tags if specified
                if tags:
                    page_tags = page.get("tags", [])
                    if not any(tag in page_tags for tag in tags):
                        continue
                
                results.append(page)
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_categories(self) -> List[str]:
        """Gibt alle verwendeten Kategorien zurück"""
        categories = set()
        for page in self.pages.values():
            if page.get("category"):
                categories.add(page["category"])
        return list(categories)
    
    async def get_all_tags(self) -> List[str]:
        """Gibt alle verwendeten Tags zurück"""
        tags = set()
        for page in self.pages.values():
            for tag in page.get("tags", []):
                tags.add(tag)
        return list(tags)
    
    async def get_recent_pages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Gibt die zuletzt aktualisierten Seiten zurück"""
        sorted_pages = sorted(
            self.pages.values(),
            key=lambda x: x.get("updated_at", ""),
            reverse=True
        )
        return sorted_pages[:limit]


# Singleton instance
_wiki_service: Optional[WikiService] = None


def get_wiki_service() -> WikiService:
    """Get or create the Wiki service singleton"""
    global _wiki_service
    if _wiki_service is None:
        _wiki_service = WikiService()
    return _wiki_service
