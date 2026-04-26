from repositories.profile_repository import ProfileRepository
from repositories.student_repository import StudentRepository
from services.gemini_service import GeminiService


class ProfileAgent:
    def __init__(
        self,
        student_repository: StudentRepository,
        profile_repository: ProfileRepository,
        gemini_service: GeminiService,
    ) -> None:
        self.student_repository = student_repository
        self.profile_repository = profile_repository
        self.gemini_service = gemini_service

    def generate_profile(self, aluno_id: int) -> dict:
        profile_input = self.student_repository.build_profile_input(aluno_id)
        if not profile_input:
            raise ValueError("Aluno nao encontrado")

        perfil_texto = self.gemini_service.analisar_perfil(profile_input)
        self.profile_repository.upsert_profile(aluno_id, perfil_texto)

        return {
            "aluno_id": aluno_id,
            "perfil_texto": perfil_texto,
        }
