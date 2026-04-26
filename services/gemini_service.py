import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from google import genai
from google.genai import types

from app.config import Settings
from utils.json_utils import extract_json_array
from utils.prompt_loader import load_prompt


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

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
        )
        return (response.text or "").strip()

    def gerar_texto(self, prompt: str, payload: dict[str, Any]) -> str:
        data = json.dumps(payload, ensure_ascii=False, default=self._json_default)
        text = self._generate([prompt, data])
        return text

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
        prompt = load_prompt("recommendation_prompt.txt")
        text = self.gerar_texto(prompt, payload)
        parsed = extract_json_array(text)

        recommendations: list[dict[str, str]] = []
        for item in parsed:
            titulo = str(item.get("titulo", "")).strip()
            motivo = str(item.get("motivo", "")).strip()
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
        transcription = self._generate(
            [
                prompt,
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ]
        )
        return transcription.strip()
