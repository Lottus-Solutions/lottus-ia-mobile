import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from google import genai
from google.genai import errors, types

from app.config import Settings
from models.bulletin import PlanoAcao
from models.recommendation import BookRecommendation
from utils.json_utils import extract_json_array
from utils.prompt_loader import load_prompt


class GeminiUnavailableError(Exception):
    """Raised when the Gemini API is temporarily overloaded or rate-limited."""


def _is_transient_error(exc: errors.APIError) -> bool:
    if isinstance(exc, errors.ServerError):
        return True
    return isinstance(exc, errors.ClientError) and exc.code == 429


class GeminiService:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.gemini_model
        self.client = (
            genai.Client(api_key=settings.gemini_api_key)
            if settings.gemini_api_key
            else None
        )

    def _generate(self, contents: list[Any]) -> str:
        if not self.client:
            return ""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
        except errors.APIError as exc:
            if _is_transient_error(exc):
                raise GeminiUnavailableError("Gemini esta sobrecarregado no momento") from exc
            raise

        return (response.text or "").strip()

    def gerar_texto(self, prompt: str, payload: dict[str, Any]) -> str:
        data = json.dumps(payload, ensure_ascii=False, default=self._json_default)
        try:
            return self._generate([prompt, data])
        except GeminiUnavailableError:
            return ""

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return str(value)

    def analisar_perfil(self, profile_data: dict[str, Any]) -> str:
        prompt = load_prompt("profile_prompt.txt")
        text = self.gerar_texto(prompt, profile_data)

        if text:
            return text

        aluno = profile_data.get("aluno", {})
        categorias = profile_data.get("categorias_favoritas", [])
        top_categoria = categorias[0]["categoria"] if categorias else "leituras variadas"
        emprestimos = profile_data.get("indicadores", {}).get("total_emprestimos", 0)
        return (
            f"{aluno.get('nome', 'Aluno')} demonstra interesse por {top_categoria}, "
            f"com {emprestimos} emprestimos registrados e evolucao de leitura em acompanhamento."
        )

    def recomendar(self, payload: dict[str, Any]) -> list[dict[str, str]]:
        if not self.client:
            return []

        prompt = load_prompt("recommendation_prompt.txt")
        data = json.dumps(payload, ensure_ascii=False, default=self._json_default)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, data],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[BookRecommendation],
                ),
            )
        except errors.APIError as exc:
            if _is_transient_error(exc):
                return []
            raise

        recommendations: list[dict[str, str]] = []
        for item in response.parsed or []:
            titulo = item.titulo.strip()
            motivo = item.motivo.strip()
            if titulo and motivo:
                recommendations.append({"titulo": titulo, "motivo": motivo[:180]})

        return recommendations[:3]

    def transcrever_audio(self, audio_bytes: bytes, mime_type: str = "audio/mpeg") -> str:
        if not self.client:
            return ""

        prompt = (
            "Transcreva o audio em portugues brasileiro, mantendo fidelidade ao que foi dito "
            "e sem adicionar interpretacoes."
        )
        try:
            transcription = self._generate(
                [
                    prompt,
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                ]
            )
        except GeminiUnavailableError:
            return ""
        return transcription.strip()

    def extrair_notas_boletim(self, pdf_bytes: bytes) -> list[dict]:
        if not self.client:
            return []

        prompt = (
            "Analise este boletim escolar e extraia todas as disciplinas com suas respectivas notas. "
            "Retorne um JSON array com objetos no formato: "
            '[{"disciplina": "nome da materia", "nota": valor_numerico, "situacao": "aprovado|recuperacao|reprovado"}]. '
            "Considere aprovado nota >= 7.0, recuperacao entre 5.0 e 6.9, reprovado abaixo de 5.0. "
            "Se nao conseguir identificar a nota numerica, use null. "
            "Retorne somente o JSON array, sem texto adicional."
        )
        text = self._generate(
            [
                prompt,
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            ]
        )
        return extract_json_array(text)

    def gerar_plano_boletim(self, payload: dict) -> dict | None:
        if not self.client:
            return None

        prompt = load_prompt("bulletin_prompt.txt")
        data = json.dumps(payload, ensure_ascii=False, default=self._json_default)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, data],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PlanoAcao,
                ),
            )
        except errors.APIError as exc:
            if _is_transient_error(exc):
                return None
            raise

        if not response.parsed:
            return None

        return response.parsed.model_dump()
