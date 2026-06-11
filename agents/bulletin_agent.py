from services.gemini_service import GeminiService
from repositories.profile_repository import ProfileRepository
from repositories.student_repository import StudentRepository


class BulletinAgent:
    def __init__(
        self,
        gemini_service: GeminiService,
        student_repository: StudentRepository,
        profile_repository: ProfileRepository,
    ) -> None:
        self.gemini_service = gemini_service
        self.student_repository = student_repository
        self.profile_repository = profile_repository

    def analyze(self, aluno_id: int, pdf_bytes: bytes) -> dict:
        student = self.student_repository.get_student(aluno_id)
        if not student:
            raise ValueError("Aluno nao encontrado")

        notas = self.gemini_service.extrair_notas_boletim(pdf_bytes)
        if not notas:
            raise ValueError("Nao foi possivel extrair notas do boletim enviado")

        notas_validas = [n for n in notas if isinstance(n.get("nota"), (int, float))]
        media_geral = (
            round(sum(n["nota"] for n in notas_validas) / len(notas_validas), 2)
            if notas_validas
            else None
        )

        profile = self.profile_repository.get_profile(aluno_id)
        if not profile:
            profile_input = self.student_repository.build_profile_input(aluno_id)
            if profile_input:
                profile_text = self.gemini_service.analisar_perfil(profile_input)
                self.profile_repository.upsert_profile(aluno_id, profile_text)
                profile = self.profile_repository.get_profile(aluno_id)

        profile_input = self.student_repository.build_profile_input(aluno_id) or {}

        plano_acao = self.gemini_service.gerar_plano_boletim(
            {
                "aluno": student,
                "perfil_leitura": (profile or {}).get("perfil_texto"),
                "indicadores_leitura": profile_input.get("indicadores", {}),
                "categorias_favoritas": profile_input.get("categorias_favoritas", []),
                "notas": notas,
                "media_geral": media_geral,
            }
        )

        if not plano_acao:
            plano_acao = {
                "diagnostico_geral": (
                    "Com base nas notas do boletim, recomendamos iniciar uma rotina de leitura diaria "
                    "de 20 minutos, priorizando textos relacionados as disciplinas com maior dificuldade."
                ),
                "disciplinas_prioritarias": [],
                "plano_semanal_leitura": [],
                "como_pais_podem_ajudar": [
                    "Acompanhe o progresso semanalmente e converse com a escola a cada 15 dias."
                ],
                "meta_30_dias": "Manter uma rotina de leitura constante para apoiar a evolucao academica.",
            }

        return {
            "aluno_id": aluno_id,
            **plano_acao,
        }
