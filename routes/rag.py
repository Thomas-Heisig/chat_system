# routes/rag.py
"""
RAG System API Routes
Endpoints for document management and RAG operations
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from services.rag import get_available_providers, get_rag_provider, DocumentProcessor, ChunkConfig
from services.rag.base_rag import Document, DocumentType
from services.settings_service import settings_service
from config.settings import logger, enhanced_logger

router = APIRouter(prefix="/api/rag", tags=["rag"])

# Document processor instance
doc_processor = DocumentProcessor()

# RAG provider instance (lazy loaded)
_rag_provider = None


async def get_rag_instance():
    """Get or create RAG provider instance"""
    global _rag_provider
    
    if _rag_provider is None:
        rag_settings = settings_service.get_rag_settings()
        provider_name = rag_settings.get('provider', 'chromadb')
        
        try:
            provider_class = get_rag_provider(provider_name)
            _rag_provider = provider_class({
                'collection_name': rag_settings.get('collection_name', 'chat_documents'),
                'persist_directory': './chroma_data',
                'embedding_dimension': 384
            })
            await _rag_provider.initialize()
        except Exception as e:
            enhanced_logger.error("Failed to initialize RAG provider", error=str(e))
            raise
    
    return _rag_provider


@router.get("/status")
async def get_rag_status():
    """Get RAG system status"""
    try:
        available_providers = get_available_providers()
        rag_settings = settings_service.get_rag_settings()
        
        status = {
            "enabled": rag_settings.get('enabled', False),
            "provider": rag_settings.get('provider', 'chromadb'),
            "available_providers": available_providers,
            "settings": rag_settings,
            "timestamp": datetime.now().isoformat()
        }
        
        # Try to get provider stats if initialized
        try:
            provider = await get_rag_instance()
            status["provider_stats"] = provider.get_stats()
            status["provider_health"] = await provider.health_check()
        except Exception as e:
            status["provider_error"] = str(e)
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_rag_providers():
    """List available RAG providers"""
    return {
        "providers": get_available_providers(),
        "current_provider": settings_service.get("rag", "provider", "chromadb")
    }


@router.post("/documents")
async def add_document(
    content: str = Form(..., description="Document content"),
    title: str = Form(None, description="Document title"),
    doc_type: str = Form("text", description="Document type"),
    metadata: str = Form("{}", description="JSON metadata")
):
    """Add a document to the RAG system"""
    try:
        import json
        
        provider = await get_rag_instance()
        
        # Parse metadata
        try:
            meta = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            # Invalid JSON or None, use empty dict
            meta = {}
        
        meta['title'] = title
        
        # Process document
        chunks = doc_processor.process_text(content, metadata=meta)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No content to process")
        
        # Add to vector store
        success = await provider.add_documents(chunks)
        
        if success:
            enhanced_logger.info("Document added to RAG", 
                               chunk_count=len(chunks),
                               doc_type=doc_type)
            return {
                "status": "added",
                "document_count": len(chunks),
                "chunk_ids": [chunk.id for chunk in chunks]
            }
        
        raise HTTPException(status_code=500, detail="Failed to add document")
        
    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to add document", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: str = Form("{}")
):
    """Upload and index a document file"""
    try:
        import json
        import tempfile
        import os
        
        provider = await get_rag_instance()
        
        # Parse metadata
        try:
            meta = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            # Invalid JSON or None, use empty dict
            meta = {}
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Process file
            meta['original_filename'] = file.filename
            meta['content_type'] = file.content_type
            
            chunks = doc_processor.process_file(tmp_path, metadata=meta)
            
            if not chunks:
                raise HTTPException(status_code=400, detail="No content extracted from file")
            
            # Add to vector store
            success = await provider.add_documents(chunks)
            
            if success:
                enhanced_logger.info("Document file uploaded and indexed",
                                   filename=file.filename,
                                   chunk_count=len(chunks))
                return {
                    "status": "uploaded",
                    "filename": file.filename,
                    "chunk_count": len(chunks),
                    "chunk_ids": [chunk.id for chunk in chunks]
                }
            
            raise HTTPException(status_code=500, detail="Failed to index document")
            
        finally:
            # Cleanup temp file
            os.unlink(tmp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to upload document", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/search")
async def search_documents(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=50, description="Number of results"),
    doc_type: str = Query(None, description="Filter by document type")
):
    """Search documents in the RAG system"""
    try:
        provider = await get_rag_instance()
        
        filters = {}
        if doc_type:
            filters['doc_type'] = doc_type
        
        results = await provider.query(query, top_k=top_k, filters=filters if filters else None)
        
        enhanced_logger.info("RAG search performed",
                           query=query[:50],
                           results_count=len(results))
        
        return {
            "query": query,
            "results": [result.to_dict() for result in results],
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        enhanced_logger.error("RAG search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the RAG system"""
    try:
        provider = await get_rag_instance()
        
        success = await provider.delete_documents([doc_id])
        
        if success:
            enhanced_logger.info("Document deleted from RAG", doc_id=doc_id)
            return {"status": "deleted", "doc_id": doc_id}
        
        raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error("Failed to delete document", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/clear")
async def clear_all_documents():
    """Clear all documents from the RAG system"""
    try:
        provider = await get_rag_instance()
        
        success = await provider.clear_collection()
        
        if success:
            enhanced_logger.info("RAG collection cleared")
            return {"status": "cleared", "timestamp": datetime.now().isoformat()}
        
        raise HTTPException(status_code=500, detail="Failed to clear collection")
        
    except Exception as e:
        enhanced_logger.error("Failed to clear RAG collection", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        provider = await get_rag_instance()
        
        stats = provider.get_stats()
        health = await provider.health_check()
        
        return {
            "stats": stats,
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        enhanced_logger.error("Failed to get RAG stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_rag_pipeline(
    query: str = Body(..., embed=True, description="Test query"),
):
    """Test the RAG pipeline with a query"""
    try:
        provider = await get_rag_instance()
        
        # Perform search
        results = await provider.query(query, top_k=3)
        
        # Build context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] (Score: {result.score:.2f}) {result.document.content[:200]}...")
        
        context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
        
        return {
            "query": query,
            "context": context,
            "results_count": len(results),
            "results": [result.to_dict() for result in results],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        enhanced_logger.error("RAG test failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_rag_config(config: Dict[str, Any] = Body(...)):
    """Update RAG configuration"""
    try:
        success = settings_service.update_rag_settings(**config)
        
        if success:
            # Reset provider to apply new settings
            global _rag_provider
            _rag_provider = None
            
            enhanced_logger.info("RAG config updated", keys=list(config.keys()))
            return {"status": "updated", "config": settings_service.get_rag_settings()}
        
        raise HTTPException(status_code=400, detail="Failed to update config")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
