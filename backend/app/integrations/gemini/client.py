from google import genai

from app.core.config import settings
from app.core.google_cloud import ensure_google_application_credentials


class GeminiClient:
    def __init__(self) -> None:
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.timeout_seconds = settings.gemini_timeout_seconds
        self.use_vertex_ai = settings.use_vertex_ai
        self.project_id = settings.google_cloud_project
        self.service_account_json = settings.google_service_account_json
        self.regions = [
            region.strip()
            for region in settings.gemini_regions.split(",")
            if region.strip()
        ]
        self.client = self._build_default_client()

    def _build_default_client(self) -> genai.Client:
        if self.use_vertex_ai and self.project_id and self.regions:
            self._ensure_vertex_credentials_file()
            return self._build_vertex_client(self.regions[0])

        return genai.Client(api_key=self.api_key)

    def _build_vertex_client(self, region: str) -> genai.Client:
        return genai.Client(
            vertexai=True,
            project=self.project_id,
            location=region,
        )

    def iter_clients(self) -> list[tuple[str, genai.Client]]:
        if self.use_vertex_ai and self.project_id and self.regions:
            self._ensure_vertex_credentials_file()
            return [
                (region, self._build_vertex_client(region))
                for region in self.regions
            ]

        return [("api-key", self.client)]

    def _ensure_vertex_credentials_file(self) -> None:
        ensure_google_application_credentials(
            service_account_json=self.service_account_json,
            fallback_credentials_file=settings.google_sheets_credentials_file,
        )
