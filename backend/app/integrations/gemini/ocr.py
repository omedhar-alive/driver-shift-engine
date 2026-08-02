import json
import logging
import traceback
import time
from pathlib import Path

from google.genai import types

from app.integrations.gemini.client import GeminiClient
from app.integrations.google_cloud_storage import GoogleCloudStorageService

logger = logging.getLogger(__name__)


class GeminiOCRService:
    LOW_CONFIDENCE_LOG_THRESHOLD = 0.85

    def __init__(self) -> None:
        self.client_wrapper = GeminiClient()
        self.model = self.client_wrapper.model
        self.storage_service = GoogleCloudStorageService()

    def extract_dashboard_values(self, image_reference: str) -> dict:
        image_content = self.storage_service.load_image(image_reference)
        if image_content is None:
            return {
                "success": False,
                "error_type": "file_not_found",
                "requires_retake": False,
                "message": "لم يتم العثور على صورة التابلوه.",
                "raw_response": None,
            }

        return self._extract_dashboard_values_from_image_bytes(
            image_bytes=image_content.content,
            mime_type=image_content.mime_type,
        )

    def extract_dashboard_values_from_bytes(self, image_bytes: bytes, mime_type: str) -> dict:
        return self._extract_dashboard_values_from_image_bytes(
            image_bytes=image_bytes,
            mime_type=mime_type,
        )

    def _extract_dashboard_values_from_image_bytes(self, image_bytes: bytes, mime_type: str) -> dict:
        prompt = """
تصرف كمدقق بيانات تليماتية عالي الدقة. مهمتك هي استخراج قيم ODO و SOC من لوحة عدادات السيارة الكهربائية المرفقة بأعلى دقة ممكنة (تصل لـ 99%).

### أولاً: التصنيف المكاني (Spatial Routing)
قم بتحليل هيكل الشاشة لتحديد البروتوكول المتبع:
1. بروتوكول [XPENG]: شاشة تابلت عرضية. ابحث عن SOC في "شريط الحالة العلوي" حصراً، داخل أو بجانب أيقونة البطارية الخضراء/الرمادية. الـ ODO يقع في الأسفل تحت عنوان "Odometer".
2. بروتوكول [BYD]: لوحة عدادات مستطيلة خلف المقود. ابحث عن SOC في الركن السفلي الأيسر فوق شريط تقدم أفقي. الـ ODO يقع في أسفل المنتصف بجانب كلمة "ODO".

### ثانياً: قواعد استخراج نسبة الشحن (SOC) - "حل مشكلة القيم المنخفضة":
1. القاعدة الذهبية: قيمة SOC هي الرقم الموجود "داخل" إطار أيقونة البطارية أو الملاصق لها تماماً.
2. غياب علامة المئوية: في حالات الشحن المنخفض (أقل من 10%) أو الصور ذات الجودة الضعيفة، قد يختفي رمز (%) بصرياً. "يُسمح ويُطلب" منك استخراج الرقم المجرد (مثل 5 أو 8) واعتباره SOC إذا وجدته داخل إطار البطارية، حتى لو لم تظهر علامة %.
3. الاستبعاد الصارم: يُمنع منعاً باتاً استخراج أي نسبة مئوية من منتصف الشاشة مرتبطة بكلمات (Driving, AC, Consumption, Lights, Other). هذه نسب استهلاك وليست نسبة شحن.
4. منطق الدعم: استخدم قيمة المسافة المتبقية (Range) كدليل منطقي؛ إذا كانت المسافة أقل من 50 كم، فتوقع يقيناً أن يكون الـ SOC رقماً أحادياً صغيراً (1-9) وربما بتباين ضعيف.

### ثالثاً: قواعد استخراج العداد الكلي (ODO):
1. ابحث عن الكلمة الدليلية (Total) أو (ODO) أو (Odometer).
2. استخرج الرقم المجاور لها كقيمة صحيحة (Integer) بدون فواصل.
3. تجاهل تماماً أرقام الـ Trip، الـ Speed (0 km/h)، والـ Range.

### رابعاً: التعامل مع جودة الصورة المنخفضة (Low-Quality Recovery):
- في حال وجود خطوط تداخل (Moiré) أو غبش، اعتمد على "الهيكل البصري" للرقم وموقعه داخل الأيقونة.
- لا تتردد في استخراج الرقم إذا كنت قادراً على تمييزه بصرياً حتى لو كانت درجة الثقة منخفضة؛ نحن نفضل "أفضل تقدير مدعوم بالمنطق" على القيمة "null".
- تجاهل أي انعكاسات ليد السائق أو الهاتف وركز على الخط الرقمي (Digital Font).

### القواعد الفنية النهائية:
- المخرجات JSON فقط.
- لا تضف أي نص أو شرح خارج الـ JSON.
- أعد القيم الرقمية كنصوص (Strings) داخل الكائن الخاص بها.
- إذا تعذر تماماً العثور على أي سند بصري للرقم، أعد "null".
- اجعل قيمة "failure_reason" باللغة العربية واشرح فيها "بناءً على أي قاعدة" تم الفشل (مثلاً: عدم وجود رقم داخل إطار البطارية).
- في حقل "visual_reasoning_log" (إن وجد في السكيما)، اشرح بالإنجليزية كيف ميزت الرقم وتجاهلت المشتتات.

كن دقيقاً وحازماً: قيمة الـ SOC في XPENG هي الرقم الصغير في أعلى الشاشة داخل البطارية، وليست الأرقام الكبيرة في المنتصف.
"""

        schema = {
            "type": "OBJECT",
            "properties": {
                "odometer": {
                    "type": "OBJECT",
                    "properties": {
                        "value": {"type": "STRING"},
                        "unit": {"type": "STRING"},
                        "confidence_score": {"type": "NUMBER"},
                    },
                    "required": ["value", "unit", "confidence_score"],
                },
                "state_of_charge": {
                    "type": "OBJECT",
                    "properties": {
                        "value": {"type": "STRING"},
                        "unit": {"type": "STRING"},
                        "confidence_score": {"type": "NUMBER"},
                    },
                    "required": ["value", "unit", "confidence_score"],
                },
                "metadata": {
                    "type": "OBJECT",
                    "properties": {
                        "is_dashboard_clear": {"type": "BOOLEAN"},
                        "failure_reason": {"type": "STRING"},
                    },
                    "required": ["is_dashboard_clear", "failure_reason"],
                },
            },
            "required": ["odometer", "state_of_charge", "metadata"],
        }

        parsed: dict | None = None
        response: types.GenerateContentResponse | None = None

        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True,
                ),
            )

            parsed, response = self._generate_with_failover(
                prompt=prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                config=config,
            )

            odometer = parsed["odometer"]
            soc = parsed["state_of_charge"]
            metadata = parsed["metadata"]

            odo_value_raw = str(odometer["value"]).strip().lower()
            soc_value_raw = str(soc["value"]).strip().lower()

            odo_confidence = float(odometer["confidence_score"])
            soc_confidence = float(soc["confidence_score"])

            failure_reason = self._normalize_nullable_string(
                metadata.get("failure_reason")
            )

            if odo_value_raw == "null" or soc_value_raw == "null":
                self._log_debug_response(
                    event="ocr_unreadable",
                    response=response,
                    parsed=parsed,
                    details={
                        "odo_value": odo_value_raw,
                        "soc_value": soc_value_raw,
                        "failure_reason": failure_reason,
                    },
                )
                return {
                    "success": False,
                    "error_type": "ocr_unreadable",
                    "requires_retake": True,
                    "message": failure_reason or "الصورة غير واضحة. يرجى إعادة تصوير التابلوه بشكل أوضح مع تقليل الانعكاس والتأكد من ظهور الأرقام بالكامل.",
                    "raw_response": self._serialize_raw_response(parsed),
                }

            if (
                odo_confidence < self.LOW_CONFIDENCE_LOG_THRESHOLD
                or soc_confidence < self.LOW_CONFIDENCE_LOG_THRESHOLD
            ):
                self._log_debug_response(
                    event="ocr_low_confidence",
                    response=response,
                    parsed=parsed,
                    details={
                        "odo_value": odo_value_raw,
                        "soc_value": soc_value_raw,
                        "odo_confidence": odo_confidence,
                        "soc_confidence": soc_confidence,
                        "failure_reason": failure_reason,
                    },
                )

            return {
                "success": True,
                "error_type": None,
                "odo": self._parse_numeric_string(odo_value_raw),
                "odo_unit": self._normalize_unit(odometer.get("unit")),
                "soc": self._parse_numeric_string(soc_value_raw),
                "soc_unit": self._normalize_unit(soc.get("unit")),
                "odo_confidence": odo_confidence,
                "soc_confidence": soc_confidence,
                "is_dashboard_clear": metadata.get("is_dashboard_clear", False),
                "failure_reason": failure_reason,
                "requires_retake": False,
                "message": "تمت قراءة صورة التابلوه بنجاح",
                "raw_response": self._serialize_raw_response(parsed),
            }

        except Exception as exc:
            payload = {
                "event": "ocr_exception",
                "model": self.model,
                "error": str(exc),
            }
            if parsed is not None:
                payload["parsed"] = parsed
            if response is not None:
                payload["response"] = json.loads(self._serialize_response_debug(response))

            logger.exception(
                "Gemini OCR error: %s",
                json.dumps(payload, ensure_ascii=False, default=str),
            )
            print(f"Gemini OCR error: {exc}")
            traceback.print_exc()
            error_text = str(exc)
            lowered = error_text.lower()

            if "429" in error_text or "rate limit" in lowered or "resource_exhausted" in lowered:
                return {
                    "success": False,
                    "error_type": "rate_limited",
                    "requires_retake": False,
                    "message": "خدمة OCR مشغولة مؤقتًا. سيتم معالجة الطلب قريبًا.",
                    "raw_response": None,
                }

            if "503" in error_text or "unavailable" in lowered or "high demand" in lowered:
                return {
                    "success": False,
                    "error_type": "provider_unavailable",
                    "requires_retake": False,
                    "message": "خدمة OCR غير متاحة مؤقتًا. سيتم معالجة الطلب قريبًا.",
                    "raw_response": None,
                }

            if "quota" in lowered:
                return {
                    "success": False,
                    "error_type": "quota_exhausted",
                    "requires_retake": False,
                    "message": "خدمة OCR غير متاحة مؤقتًا. سيتم معالجة الطلب قريبًا.",
                    "raw_response": None,
                }

            return {
                "success": False,
                "error_type": "ocr_failed",
                "requires_retake": False,
                "message": "تعذر تحليل الصورة حاليًا. حاول مرة أخرى لاحقًا.",
                "raw_response": None,
            }

    def _parse_numeric_string(self, value: str) -> float:
        cleaned = value.strip()
        cleaned = cleaned.replace(",", "")
        cleaned = cleaned.replace("%", "")
        cleaned = cleaned.replace("km", "")
        cleaned = cleaned.replace("mi", "")
        cleaned = cleaned.strip()
        return float(cleaned)

    def _normalize_nullable_string(self, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = str(value).strip()
        if cleaned == "" or cleaned.lower() == "null":
            return None

        return cleaned

    def _normalize_unit(self, unit: str | None) -> str | None:
        normalized = self._normalize_nullable_string(unit)
        if normalized is None:
            return None

        lowered = normalized.lower()
        if lowered == "%":
            return "percent"

        return lowered

    def _serialize_raw_response(self, parsed: dict) -> str:
        return json.dumps(parsed, ensure_ascii=False)

    def _serialize_response_debug(self, response: types.GenerateContentResponse) -> str:
        dumped = response.model_dump(
            exclude={"sdk_http_response"},
            exclude_none=True,
            mode="json",
        )
        return json.dumps(dumped, ensure_ascii=False, default=str)

    def _log_debug_response(
        self,
        event: str,
        response: types.GenerateContentResponse,
        parsed: dict,
        details: dict | None = None,
    ) -> None:
        payload = {
            "event": event,
            "model": self.model,
            "parsed": parsed,
            "response": json.loads(self._serialize_response_debug(response)),
        }
        if details:
            payload["details"] = details

        logger.warning(
            "Gemini OCR debug: %s",
            json.dumps(payload, ensure_ascii=False, default=str),
        )

    def _generate_with_failover(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str,
        config: types.GenerateContentConfig,
    ) -> tuple[dict, types.GenerateContentResponse]:
        last_exception: Exception | None = None

        for region, client in self.client_wrapper.iter_clients():
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    ],
                    config=config,
                )

                parsed = response.parsed

                if parsed is None:
                    self._log_debug_response(
                        event="empty_parsed_response",
                        response=response,
                        parsed={},
                        details={"region": region},
                    )
                    raise ValueError("Gemini returned an empty parsed response.")

                if hasattr(parsed, "model_dump"):
                    return parsed.model_dump(), response

                return parsed, response
            except Exception as exc:
                last_exception = exc
                error_text = str(exc)
                lowered = error_text.lower()

                if "503" in error_text or "overloaded" in lowered or "unavailable" in lowered:
                    print(f"Gemini region {region} unavailable, trying next region if any.")
                    continue

                if "429" in error_text or "rate limit" in lowered or "resource_exhausted" in lowered:
                    print(f"Gemini region {region} rate limited, retrying next region after backoff.")
                    time.sleep(2)
                    continue

                raise

        if last_exception is not None:
            raise last_exception

        raise ValueError("No Gemini clients were configured.")

    def resolve_mime_type(self, image_path: Path) -> str:
        suffix = image_path.suffix.lower()

        if suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"

        if suffix == ".png":
            return "image/png"

        if suffix == ".webp":
            return "image/webp"

        return "image/jpeg"
