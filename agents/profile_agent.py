from recomendador import gerar_embedding_texto, salvar_perfil_leitura
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
        embedding = gerar_embedding_texto(perfil_texto)
        salvar_perfil_leitura(aluno_id, perfil_texto, embedding, db=self.profile_repository.db)

        return {
            "aluno_id": aluno_id,
            "perfil_texto": perfil_texto,
        }
