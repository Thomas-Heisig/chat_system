import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile

from config.settings import enhanced_logger, logger, settings
from database.models import File, FileType, create_file
from database.repositories import FileRepository, ProjectRepository, UserRepository


class FileService:
    def __init__(self, file_repository: FileRepository):
        self.file_repo = file_repository
        self.project_repo = ProjectRepository()
        self.user_repo = UserRepository()

        # Ensure upload directory exists - Korrigiert: settings.UPLOAD_FOLDER
        Path(settings.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

        logger.info("🔄 FileService initialized")

    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in settings.ALLOWED_EXTENSIONS
        )  # Korrigiert: settings.ALLOWED_EXTENSIONS

    async def save_uploaded_file(
        self,
        file: UploadFile,
        username: str,
        project_id: Optional[str] = None,
        ticket_id: Optional[str] = None,
        description: Optional[str] = None,
        is_public: bool = False,
    ) -> File:
        """Save uploaded file and create database record"""
        start_time = datetime.now()

        try:
            if not file or not file.filename:
                raise ValueError("No file provided")

            if not self.allowed_file(file.filename):
                raise ValueError(f"File type not allowed: {file.filename}")

            # Generate unique filename
            file_extension = file.filename.rsplit(".", 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(settings.UPLOAD_FOLDER, unique_filename)  # Korrigiert

            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)

            # Determine file type (for future validation)
            _file_type = self._determine_file_type(file.filename, file.content_type)

            # Create file record
            safe_mime_type = file.content_type or "application/octet-stream"
            file_record = create_file(
                original_filename=file.filename,
                stored_filename=unique_filename,
                file_path=file_path,
                file_size=len(content),
                file_hash=file_hash,
                mime_type=safe_mime_type,
                uploaded_by=username,
                project_id=project_id,
                ticket_id=ticket_id,
                description=description,
                is_public=is_public,
            )

            file_id = self.file_repo.save_file(file_record)
            file_record.id = file_id

            duration = (datetime.now() - start_time).total_seconds()
            enhanced_logger.info(
                "File uploaded successfully",
                file_id=file_id,
                filename=file.filename,
                file_size=len(content),
                uploaded_by=username,
                project_id=project_id,
                duration=duration,
            )
            return file_record

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            enhanced_logger.error(
                "Failed to upload file",
                error=str(e),
                filename=file.filename if file else "unknown",
                duration=duration,
            )
            raise

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _determine_file_type(self, filename: str, mime_type: Optional[str]) -> FileType:
        """Determine file type from filename and MIME type"""
        # Check by MIME type first
        if mime_type and mime_type.startswith("image/"):
            return FileType.IMAGE
        elif mime_type and mime_type.startswith("audio/"):
            return FileType.AUDIO
        elif mime_type and mime_type.startswith("video/"):
            return FileType.VIDEO
        elif mime_type and mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            return FileType.DOCUMENT
        elif mime_type and (mime_type.startswith("text/") or "code" in mime_type):
            return FileType.CODE
        elif mime_type and (
            mime_type.startswith("application/zip") or mime_type.startswith("application/x-rar")
        ):
            return FileType.ARCHIVE

        # Fallback to filename extension
        extension = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        if extension in ["csv", "json", "xml", "xlsx", "xls"]:
            return FileType.DATA

        return FileType.OTHER

    def get_file(self, file_id: str) -> Optional[File]:
        """Get file by ID"""
        try:
            file_record = self.file_repo.get_file(file_id)
            if file_record:
                logger.debug(f"📄 Retrieved file: {file_record.original_filename}")
            return file_record
        except Exception as e:
            logger.error(f"❌ Failed to get file {file_id}: {e}")
            return None

    def get_project_files(self, project_id: str) -> List[File]:
        """Get all files for a project"""
        try:
            # Retrieve files for the given project using file_repo.get_files with a filter
            project_files = [
                file for file in self.file_repo.get_files() if file.project_id == project_id
            ]

            logger.info(f"✅ Retrieved {len(project_files)} files for project {project_id}")
            return project_files

        except Exception as e:
            logger.error(f"❌ Failed to get project files: {e}")
            return []

    def analyze_uploaded_file(self, file_id: str) -> Dict[str, Any]:
        """Analyze uploaded file (background task)"""
        try:
            file_record = self.file_repo.get_file(file_id)
            if not file_record:
                return {"error": "File not found"}

            analysis = {
                "file_id": file_id,
                "filename": file_record.original_filename,
                "file_type": file_record.file_type.value,
                "file_size": file_record.file_size,
                "uploaded_by": file_record.uploaded_by,
                "upload_date": (
                    file_record.upload_date.isoformat() if file_record.upload_date else None
                ),
                "analysis_date": datetime.now().isoformat(),
            }

            # Basic text file analysis
            if file_record.file_type == FileType.DOCUMENT or (
                file_record.mime_type and file_record.mime_type.startswith("text/")
            ):
                analysis.update(self._analyze_text_file(file_record.file_path))
            elif file_record.file_type == FileType.IMAGE:
                analysis.update(self._analyze_image_file(file_record))
            elif file_record.file_type == FileType.CODE:
                analysis.update(self._analyze_code_file(file_record.file_path))

            logger.info(f"🔍 File analysis completed for {file_record.original_filename}")
            return analysis

        except Exception as e:
            logger.error(f"❌ Error analyzing file {file_id}: {e}")
            return {"error": str(e)}

    def _analyze_text_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze text file content"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "content_type": "text",
                "word_count": len(content.split()),
                "line_count": len(content.splitlines()),
                "character_count": len(content),
                "content_preview": content[:500] + "..." if len(content) > 500 else content,
            }

            # Simple sentiment analysis based on keywords
            positive_words = ["good", "great", "excellent", "awesome", "amazing"]
            negative_words = ["bad", "terrible", "awful", "horrible", "poor"]

            content_lower = content.lower()
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)

            if positive_count > negative_count:
                analysis["sentiment"] = "positive"
            elif negative_count > positive_count:
                analysis["sentiment"] = "negative"
            else:
                analysis["sentiment"] = "neutral"

            analysis["sentiment_score"] = positive_count - negative_count

            return analysis

        except Exception as e:
            logger.error(f"❌ Error analyzing text file: {e}")
            return {"content_analysis_error": str(e)}

    def _analyze_image_file(self, file_record: File) -> Dict[str, Any]:
        """Analyze image file"""
        analysis = {
            "content_type": "image",
            "analysis_available": "basic",
            "note": "Advanced image analysis requires PIL/Pillow and vision AI models",
        }

        # Basic analysis based on file extension and size
        extension = (
            file_record.original_filename.rsplit(".", 1)[1].upper()
            if "." in file_record.original_filename
            else "Unknown"
        )
        analysis["format"] = extension
        analysis["size_category"] = (
            "small"
            if file_record.file_size < 1024 * 1024
            else "medium" if file_record.file_size < 10 * 1024 * 1024 else "large"
        )

        return analysis

    def _analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze code file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()
            analysis = {
                "content_type": "code",
                "line_count": len(lines),
                "character_count": len(content),
                "non_empty_lines": len([line for line in lines if line.strip()]),
                "estimated_complexity": (
                    "low" if len(lines) < 50 else "medium" if len(lines) < 200 else "high"
                ),
            }

            # Simple code structure analysis
            analysis["has_functions"] = any("def " in line for line in lines)
            analysis["has_classes"] = any("class " in line for line in lines)
            analysis["has_comments"] = any(line.strip().startswith("#") for line in lines)

            return analysis

        except Exception as e:
            logger.error(f"❌ Error analyzing code file: {e}")
            return {"code_analysis_error": str(e)}

    def increment_download_count(self, file_id: str) -> bool:
        """Increment file download count"""
        try:
            self.file_repo.increment_download_count(file_id)
            logger.debug(f"📥 Incremented download count for file {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to increment download count: {e}")
            return False

    def get_file_download_info(self, file_id: str) -> Dict[str, Any]:
        """Get file information for download"""
        try:
            file_record = self.get_file(file_id)
            if not file_record:
                return {"error": "File not found"}

            return file_record.to_download_dict()

        except Exception as e:
            logger.error(f"❌ Failed to get file download info: {e}")
            return {"error": str(e)}

    def cleanup_orphaned_files(self, days_old: int = 30) -> int:
        """Clean up orphaned files (not linked to any project or ticket)"""
        try:
            # This would typically call file_repo.cleanup_orphaned_files(days_old)
            logger.info(f"🧹 Cleaning up orphaned files older than {days_old} days")
            # Implementation would go here
            return 0

        except Exception as e:
            logger.error(f"❌ Failed to cleanup orphaned files: {e}")
            return 0
