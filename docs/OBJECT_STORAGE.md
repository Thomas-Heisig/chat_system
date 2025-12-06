# Object Storage Integration

## Overview

This document describes how to configure object storage for the Chat System, supporting S3, MinIO, and local filesystem storage with graceful fallback.

## Configuration

### Environment Variables

```bash
# Object Storage Configuration
OBJECT_STORAGE_ENABLED=false  # Enable object storage
OBJECT_STORAGE_PROVIDER=s3  # Options: s3, minio, local
OBJECT_STORAGE_BUCKET=chat-system  # Bucket/container name
OBJECT_STORAGE_ENDPOINT=  # Custom endpoint (for MinIO or S3-compatible)
OBJECT_STORAGE_ACCESS_KEY=  # Access key/ID
OBJECT_STORAGE_SECRET_KEY=  # Secret key
OBJECT_STORAGE_REGION=us-east-1  # AWS region (for S3)

# Local Storage Fallback
LOCAL_STORAGE_PATH=./uploads  # Used when object storage is disabled
```

### Settings in Code

```python
from config.settings import infrastructure_config

# Check object storage configuration
if infrastructure_config.object_storage_enabled:
    provider = infrastructure_config.object_storage_provider
    bucket = infrastructure_config.object_storage_bucket
```

## Fallback Behavior

When object storage is disabled or unavailable:
- **Local Filesystem:** Files stored in local `uploads/` directory
- **No Errors:** System continues normally
- **Automatic Fallback:** Upload operations use local storage
- **Backward Compatible:** Existing local files remain accessible

## Supported Providers

### 1. Amazon S3

**Features:**
- Highly scalable
- Global availability
- Integrated with AWS ecosystem
- Lifecycle policies

**Configuration:**
```bash
OBJECT_STORAGE_ENABLED=true
OBJECT_STORAGE_PROVIDER=s3
OBJECT_STORAGE_BUCKET=my-chat-system-bucket
OBJECT_STORAGE_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
OBJECT_STORAGE_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
OBJECT_STORAGE_REGION=us-east-1
```

**Setup:**
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Create bucket
aws s3 mb s3://my-chat-system-bucket

# Set public access block (if needed)
aws s3api put-public-access-block \
  --bucket my-chat-system-bucket \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. MinIO (Self-Hosted S3-Compatible)

**Features:**
- Open source
- S3-compatible API
- Self-hosted
- Cost-effective

**Configuration:**
```bash
OBJECT_STORAGE_ENABLED=true
OBJECT_STORAGE_PROVIDER=minio
OBJECT_STORAGE_BUCKET=chat-system
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=minioadmin
```

**Setup with Docker:**
```bash
# Start MinIO
docker run -d \
  --name minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v minio-data:/data \
  minio/minio server /data --console-address ":9001"

# Create bucket
docker exec minio \
  mc mb /data/chat-system
```

**Docker Compose:**
```yaml
services:
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"

volumes:
  minio-data:
```

### 3. Local Filesystem (Default Fallback)

**Features:**
- No external dependencies
- Simple setup
- Good for development
- No additional costs

**Configuration:**
```bash
OBJECT_STORAGE_ENABLED=false
LOCAL_STORAGE_PATH=./uploads
```

## Implementation

### Storage Service

```python
# services/storage_service.py
from pathlib import Path
from typing import Optional, BinaryIO
import boto3
from config.settings import infrastructure_config, logger

class StorageService:
    """
    Unified storage service with multi-provider support and fallback.
    """
    
    def __init__(self):
        self.enabled = infrastructure_config.object_storage_enabled
        self.provider = infrastructure_config.object_storage_provider
        self.bucket = infrastructure_config.object_storage_bucket
        self.local_path = Path("./uploads")
        self.local_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize provider-specific client
        if self.enabled:
            if self.provider in ["s3", "minio"]:
                self.client = self._init_s3_client()
            else:
                logger.warning(f"Unknown provider: {self.provider}, using local storage")
                self.enabled = False
        else:
            self.client = None
        
        logger.info(
            f"💾 Storage Service initialized "
            f"(provider: {self.provider if self.enabled else 'local'}, "
            f"fallback: {not self.enabled})"
        )
    
    def _init_s3_client(self):
        """Initialize S3/MinIO client"""
        try:
            config = {
                "aws_access_key_id": infrastructure_config.object_storage_access_key,
                "aws_secret_access_key": infrastructure_config.object_storage_secret_key,
            }
            
            if infrastructure_config.object_storage_endpoint:
                config["endpoint_url"] = infrastructure_config.object_storage_endpoint
            else:
                config["region_name"] = infrastructure_config.object_storage_region or "us-east-1"
            
            return boto3.client("s3", **config)
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.enabled = False
            return None
    
    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload file to storage with automatic fallback.
        
        Args:
            file: File object to upload
            key: Storage key/path
            content_type: MIME type of file
        
        Returns:
            Upload result with URL and metadata
        """
        if self.enabled and self.client:
            try:
                return await self._upload_to_object_storage(file, key, content_type)
            except Exception as e:
                logger.error(f"Object storage upload failed: {e}, falling back to local")
                return await self._upload_to_local(file, key)
        else:
            return await self._upload_to_local(file, key)
    
    async def _upload_to_object_storage(
        self,
        file: BinaryIO,
        key: str,
        content_type: Optional[str]
    ) -> dict:
        """Upload to S3/MinIO"""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        
        self.client.upload_fileobj(
            file,
            self.bucket,
            key,
            ExtraArgs=extra_args
        )
        
        # Generate URL
        if self.provider == "s3":
            url = f"https://{self.bucket}.s3.amazonaws.com/{key}"
        else:
            endpoint = infrastructure_config.object_storage_endpoint
            url = f"{endpoint}/{self.bucket}/{key}"
        
        logger.info(f"File uploaded to object storage: {key}")
        
        return {
            "success": True,
            "fallback": False,
            "provider": self.provider,
            "url": url,
            "key": key,
            "bucket": self.bucket,
        }
    
    async def _upload_to_local(self, file: BinaryIO, key: str) -> dict:
        """Upload to local filesystem (fallback)"""
        file_path = self.local_path / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(file.read())
        
        logger.info(f"File uploaded to local storage: {key}")
        
        return {
            "success": True,
            "fallback": True,
            "provider": "local",
            "url": f"/uploads/{key}",
            "key": key,
            "path": str(file_path),
        }
    
    async def download_file(self, key: str) -> Optional[bytes]:
        """Download file from storage with fallback"""
        if self.enabled and self.client:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=key)
                return response["Body"].read()
            except Exception as e:
                logger.error(f"Object storage download failed: {e}")
        
        # Fallback to local
        file_path = self.local_path / key
        if file_path.exists():
            return file_path.read_bytes()
        
        return None
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from storage"""
        if self.enabled and self.client:
            try:
                self.client.delete_object(Bucket=self.bucket, Key=key)
                return True
            except Exception as e:
                logger.error(f"Object storage delete failed: {e}")
        
        # Fallback to local
        file_path = self.local_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    async def list_files(self, prefix: str = "") -> list:
        """List files in storage"""
        if self.enabled and self.client:
            try:
                response = self.client.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=prefix
                )
                return [obj["Key"] for obj in response.get("Contents", [])]
            except Exception as e:
                logger.error(f"Object storage list failed: {e}")
        
        # Fallback to local
        if prefix:
            path = self.local_path / prefix
        else:
            path = self.local_path
        
        if path.exists():
            return [str(p.relative_to(self.local_path)) for p in path.rglob("*") if p.is_file()]
        
        return []
    
    def get_status(self) -> dict:
        """Get storage service status"""
        return {
            "service": "storage",
            "enabled": self.enabled,
            "provider": self.provider if self.enabled else "local",
            "bucket": self.bucket if self.enabled else None,
            "fallback_mode": not self.enabled,
            "configuration": {
                "OBJECT_STORAGE_ENABLED": self.enabled,
                "OBJECT_STORAGE_PROVIDER": self.provider,
                "OBJECT_STORAGE_BUCKET": self.bucket,
                "LOCAL_STORAGE_PATH": str(self.local_path),
            }
        }


# Singleton
_storage_service: Optional[StorageService] = None

def get_storage_service() -> StorageService:
    """Get or create storage service singleton"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
```

### Using the Storage Service

```python
from services.storage_service import get_storage_service

storage = get_storage_service()

# Upload file
with open("image.jpg", "rb") as f:
    result = await storage.upload_file(
        f,
        key="uploads/images/image.jpg",
        content_type="image/jpeg"
    )

# Download file
data = await storage.download_file("uploads/images/image.jpg")

# Delete file
success = await storage.delete_file("uploads/images/image.jpg")

# List files
files = await storage.list_files(prefix="uploads/images/")
```

## Pre-Signed URLs

For secure, temporary access to private files:

```python
def generate_presigned_url(key: str, expiration: int = 3600) -> str:
    """
    Generate pre-signed URL for temporary access.
    
    Args:
        key: Object key
        expiration: URL expiration in seconds
    
    Returns:
        Pre-signed URL
    """
    if storage.enabled and storage.client:
        try:
            url = storage.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": storage.bucket, "Key": key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
    
    # Fallback: return local path
    return f"/uploads/{key}"
```

## Lifecycle Policies

### S3 Lifecycle Configuration

```python
# scripts/configure_s3_lifecycle.py
import boto3

s3 = boto3.client("s3")

lifecycle_config = {
    "Rules": [
        {
            "Id": "DeleteOldFiles",
            "Status": "Enabled",
            "Prefix": "uploads/temp/",
            "Expiration": {"Days": 7}
        },
        {
            "Id": "TransitionToIA",
            "Status": "Enabled",
            "Prefix": "uploads/archive/",
            "Transitions": [
                {"Days": 30, "StorageClass": "STANDARD_IA"},
                {"Days": 90, "StorageClass": "GLACIER"}
            ]
        }
    ]
}

s3.put_bucket_lifecycle_configuration(
    Bucket="my-chat-system-bucket",
    LifecycleConfiguration=lifecycle_config
)
```

## Cost Optimization

### 1. Use Appropriate Storage Classes

```python
# Upload with storage class
storage.client.upload_fileobj(
    file,
    bucket,
    key,
    ExtraArgs={"StorageClass": "STANDARD_IA"}  # Infrequent Access
)
```

### 2. Compress Files Before Upload

```python
import gzip

def upload_compressed(file_path: str, key: str):
    """Upload file with compression"""
    with open(file_path, "rb") as f_in:
        with gzip.open(f"{key}.gz", "wb") as f_out:
            f_out.writelines(f_in)
    
    with open(f"{key}.gz", "rb") as f:
        storage.upload_file(f, f"{key}.gz", "application/gzip")
```

### 3. Set Expiration for Temporary Files

```python
# Upload with expiration
storage.client.upload_fileobj(
    file,
    bucket,
    key,
    ExtraArgs={"Expires": datetime.now() + timedelta(days=7)}
)
```

## Migration

### Migrate from Local to Object Storage

```python
# scripts/migrate_to_object_storage.py
from pathlib import Path
from services.storage_service import get_storage_service

async def migrate_files():
    """Migrate local files to object storage"""
    storage = get_storage_service()
    local_path = Path("./uploads")
    
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            key = str(file_path.relative_to(local_path))
            
            with open(file_path, "rb") as f:
                result = await storage.upload_file(f, key)
                
                if result["success"]:
                    print(f"Migrated: {key}")
                else:
                    print(f"Failed: {key}")
```

## Monitoring

### Storage Metrics

```python
async def get_storage_metrics():
    """Get storage usage metrics"""
    storage = get_storage_service()
    
    if not storage.enabled:
        # Local storage metrics
        total_size = sum(
            f.stat().st_size 
            for f in storage.local_path.rglob("*") 
            if f.is_file()
        )
        file_count = sum(1 for f in storage.local_path.rglob("*") if f.is_file())
        
        return {
            "provider": "local",
            "total_size_bytes": total_size,
            "total_size_mb": total_size / 1024 / 1024,
            "file_count": file_count,
        }
    
    # Object storage metrics
    response = storage.client.list_objects_v2(Bucket=storage.bucket)
    
    total_size = sum(obj["Size"] for obj in response.get("Contents", []))
    file_count = response.get("KeyCount", 0)
    
    return {
        "provider": storage.provider,
        "bucket": storage.bucket,
        "total_size_bytes": total_size,
        "total_size_mb": total_size / 1024 / 1024,
        "file_count": file_count,
    }
```

## Best Practices

1. **Use Object Storage in Production:** More scalable than local filesystem
2. **Enable Versioning:** Protect against accidental deletion
3. **Set Lifecycle Policies:** Automatically manage old files
4. **Use CDN:** Add CloudFront/CloudFlare for better performance
5. **Implement Backup:** Regular backups of critical data
6. **Monitor Costs:** Track storage and transfer costs
7. **Test Fallback:** Ensure system works with local storage

## Troubleshooting

### Connection Failed

**Solutions:**
1. Verify credentials
2. Check endpoint URL
3. Verify network connectivity
4. Check bucket permissions

**Fallback:** Automatically uses local storage

### Permission Denied

**Solutions:**
1. Verify IAM permissions (S3)
2. Check bucket policy
3. Verify access key has write permissions

### High Costs

**Solutions:**
1. Review lifecycle policies
2. Enable compression
3. Use appropriate storage classes
4. Delete unnecessary files

## Related Documentation

- [File Upload Guide](docs/FILE_UPLOAD.md)
- [Performance Optimization](PERFORMANCE.md)
- [Deployment Guide](DEPLOYMENT.md)

**Note:** Object storage is optional. Set `OBJECT_STORAGE_ENABLED=false` to use local filesystem with no loss of functionality.
