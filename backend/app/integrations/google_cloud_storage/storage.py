import mimetypes
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse
from uuid import uuid4

from app.core.config import settings
from app.core.google_cloud import ensure_google_application_credentials

try:
    from google.api_core.exceptions import NotFound
    from google.cloud import storage
except ImportError:  # pragma: no cover - dependency is installed via requirements
    NotFound = None
    storage = None


SUPPORTED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@dataclass(frozen=True)
class StoredDashboardImage:
    filename: str
    object_path: str
    public_url: str
    mime_type: str


@dataclass(frozen=True)
class StoredImageBytes:
    content: bytes
    mime_type: str


@dataclass(frozen=True)
class GCSObjectReference:
    bucket_name: str
    object_path: str


class GoogleCloudStorageService:
    def __init__(self) -> None:
        self.bucket_name = settings.google_cloud_storage_bucket_name
        self.images_prefix = settings.google_cloud_storage_dashboard_images_prefix.strip("/")
        self.project_id = settings.google_cloud_project
        self.service_account_json = settings.google_service_account_json
        self._client: Any | None = None

    def upload_dashboard_image(
        self,
        content: bytes,
        content_type: str,
    ) -> StoredDashboardImage:
        if not content:
            raise ValueError("Uploaded file is empty.")

        extension = self._resolve_extension(content_type)
        object_path = self.generate_object_path(extension)
        bucket = self._get_bucket(self._require_bucket_name())
        blob = bucket.blob(object_path)
        blob.upload_from_string(content, content_type=content_type)

        return StoredDashboardImage(
            filename=Path(object_path).name,
            object_path=object_path,
            public_url=self.build_public_url(object_path),
            mime_type=content_type,
        )

    def generate_object_path(self, extension: str) -> str:
        today = datetime.now(UTC)
        path_parts = [
            part
            for part in [
                self.images_prefix,
                today.strftime("%Y"),
                today.strftime("%m"),
                today.strftime("%d"),
            ]
            if part
        ]
        path_parts.append(f"{uuid4()}{extension}")
        return "/".join(path_parts)

    def build_public_url(self, object_path: str) -> str:
        bucket_name = self._require_bucket_name()
        return f"https://storage.googleapis.com/{bucket_name}/{quote(object_path, safe='/')}"

    def load_image(self, image_reference: str) -> StoredImageBytes | None:
        local_path = Path(image_reference)
        if local_path.exists():
            return StoredImageBytes(
                content=local_path.read_bytes(),
                mime_type=self.resolve_mime_type(local_path.name),
            )

        gcs_reference = self._resolve_gcs_reference(image_reference)
        if gcs_reference is None:
            return None

        try:
            content = (
                self._get_bucket(gcs_reference.bucket_name)
                .blob(gcs_reference.object_path)
                .download_as_bytes()
            )
        except Exception as exc:
            if NotFound is not None and isinstance(exc, NotFound):
                return None
            raise

        return StoredImageBytes(
            content=content,
            mime_type=self.resolve_mime_type(gcs_reference.object_path),
        )

    def resolve_mime_type(self, reference: str) -> str:
        mime_type, _ = mimetypes.guess_type(reference)
        if mime_type in SUPPORTED_IMAGE_CONTENT_TYPES:
            return mime_type
        return "image/jpeg"

    def _resolve_extension(self, content_type: str) -> str:
        extension = SUPPORTED_IMAGE_CONTENT_TYPES.get(content_type)
        if extension is None:
            raise ValueError(
                "Unsupported file type. Please upload JPG, PNG, or WEBP."
            )
        return extension

    def _resolve_gcs_reference(self, image_reference: str) -> GCSObjectReference | None:
        parsed = urlparse(image_reference)

        if parsed.scheme == "gs":
            bucket_name = parsed.netloc.strip()
            object_path = unquote(parsed.path.lstrip("/"))
            if not bucket_name or not object_path:
                return None
            return GCSObjectReference(bucket_name=bucket_name, object_path=object_path)

        if parsed.scheme in {"http", "https"}:
            host = parsed.netloc.strip().lower()
            path = parsed.path.lstrip("/")

            if host == "storage.googleapis.com":
                parts = path.split("/", 1)
                if len(parts) != 2:
                    return None
                bucket_name, object_path = parts
                object_path = unquote(object_path)
                if not bucket_name or not object_path:
                    return None
                return GCSObjectReference(bucket_name=bucket_name, object_path=object_path)

            public_host_suffix = ".storage.googleapis.com"
            if host.endswith(public_host_suffix):
                bucket_name = host.removesuffix(public_host_suffix)
                object_path = unquote(path)
                if not bucket_name or not object_path:
                    return None
                return GCSObjectReference(bucket_name=bucket_name, object_path=object_path)

            return None

        object_path = image_reference.strip().lstrip("/")
        if not object_path or not self.bucket_name:
            return None

        return GCSObjectReference(
            bucket_name=self.bucket_name,
            object_path=object_path,
        )

    def _get_bucket(self, bucket_name: str) -> Any:
        return self._get_client().bucket(bucket_name)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        if storage is None:
            raise RuntimeError(
                "google-cloud-storage is not installed. Install backend requirements first."
            )

        ensure_google_application_credentials(
            service_account_json=self.service_account_json,
            fallback_credentials_file=settings.google_sheets_credentials_file,
        )
        self._client = storage.Client(project=self.project_id or None)
        return self._client

    def _require_bucket_name(self) -> str:
        if not self.bucket_name:
            raise RuntimeError("GOOGLE_CLOUD_STORAGE_BUCKET_NAME is not configured.")
        return self.bucket_name
