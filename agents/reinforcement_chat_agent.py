from services.gemini_service import GeminiService
from repositories.profile_repository import ProfileRepository
from repositories.student_repository import StudentRepository
from utils.prompt_loader import load_prompt


class ReinforcementChatAgent:
    def __init__(
        self,
        gemini_service: GeminiService,
        student_repository: StudentRepository,
        profile_repository: ProfileRepository,
    ) -> None:
        self.gemini_service = gemini_service
        self.student_repository = student_repository
        self.profile_repository = profile_repository

    def respond(
        self,
        aluno_id: int,
        texto: str | None = None,
        audio_bytes: bytes | None = None,
        mime_type: str = "audio/mpeg",
    ) -> dict:
        student = self.student_repository.get_student(aluno_id)
        if not student:
            raise ValueError("Aluno nao encontrado")

        transcricao = ""
        if audio_bytes:
            transcricao = self.gemini_service.transcrever_audio(audio_bytes, mime_type)

        mensagem_base = (texto or "").strip() or transcricao.strip()
        if not mensagem_base:
            raise ValueError("Nenhum texto ou audio valido foi enviado")

        profile = self.profile_repository.get_profile(aluno_id)
        if not profile:
            profile_input = self.student_repository.build_profile_input(aluno_id)
            if profile_input:
                profile_text = self.gemini_service.analisar_perfil(profile_input)
                self.profile_repository.upsert_profile(aluno_id, profile_text)
                profile = self.profile_repository.get_profile(aluno_id)

        profile_input = self.student_repository.build_profile_input(aluno_id) or {}

        prompt = load_prompt("reinforcement_prompt.txt")
        resposta = self.gemini_service.gerar_texto(
            prompt,
            {
                "aluno": student,
                "perfil_leitura": (profile or {}).get("perfil_texto"),
                "indicadores_leitura": profile_input.get("indicadores", {}),
                "categorias_favoritas": profile_input.get("categorias_favoritas", []),
                "historico_leitura_recente": profile_input.get("emprestimos", [])[:3],
                "mensagem_responsavel": mensagem_base,
                "objetivo": "melhorar desempenho escolar com leitura orientada",
            },
        )

        if not resposta:
            resposta = (
                "Entendi sua preocupacao. Vamos iniciar uma rotina de 20 minutos de leitura, 4 vezes por semana, "
                "com textos curtos e acompanhamento de compreensao. Anote dificuldades e converse com a escola "
                "a cada 15 dias para ajustar o plano."
            )

        return {
            "aluno_id": aluno_id,
            "entrada_processada": mensagem_base,
            "transcricao": transcricao or None,
            "resposta": resposta,
        }
