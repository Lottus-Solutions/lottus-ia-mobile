from typing import Any

from models.recommendation import BookRecommendation
from repositories.book_repository import BookRepository
from repositories.profile_repository import ProfileRepository
from repositories.student_repository import StudentRepository
from services.gemini_service import GeminiService


class RecommendationAgent:
    MAX_CANDIDATE_BOOKS = 200

    def __init__(
        self,
        student_repository: StudentRepository,
        profile_repository: ProfileRepository,
        book_repository: BookRepository,
        gemini_service: GeminiService,
    ) -> None:
        self.student_repository = student_repository
        self.profile_repository = profile_repository
        self.book_repository = book_repository
        self.gemini_service = gemini_service

    def recommend(self, aluno_id: int) -> list[dict[str, str]]:
        student = self.student_repository.get_student(aluno_id)
        if not student:
            raise ValueError("Aluno nao encontrado")

        profile = self.profile_repository.get_profile(aluno_id)
        if not profile:
            generated = self.student_repository.build_profile_input(aluno_id)
            if generated:
                text = self.gemini_service.analisar_perfil(generated)
                self.profile_repository.upsert_profile(aluno_id, text)
                profile = self.profile_repository.get_profile(aluno_id)

        history = self.student_repository.get_reading_history(aluno_id)
        categories = self.student_repository.get_category_preferences(aluno_id)
        favorite_categories = [item.get("categoria") for item in categories if item.get("categoria")]
        unread_books = self.book_repository.get_unread_books(
            aluno_id,
            preferred_categories=favorite_categories,
            limit=self.MAX_CANDIDATE_BOOKS,
        )

        history_context = [
            {
                "titulo": item.get("titulo"),
                "categoria": item.get("categoria"),
                "status_emprestimo": item.get("status_emprestimo"),
                "dias_atrasados": item.get("dias_atrasados"),
            }
            for item in history[:8]
        ]
        slim_books = [
            {
                "id": book.get("id"),
                "titulo": book.get("titulo"),
                "categoria": book.get("categoria"),
                "total_paginas": book.get("total_paginas"),
                "disponivel": book.get("disponivel"),
            }
            for book in unread_books
        ]

        payload = {
            "aluno": student,
            "perfil": profile,
            "historico": history_context,
            "categorias_favoritas": categories[:5],
            "livros_candidatos": slim_books,
        }

        recommendations = self.gemini_service.recomendar(payload)
        fallback_items = [
            item.to_dict() for item in self._fallback_recommendations(unread_books, categories)
        ]

        if recommendations:
            filtered = [
                rec
                for rec in recommendations
                if any(book["titulo"] == rec["titulo"] for book in unread_books)
            ]

            if filtered:
                selected_titles = {item["titulo"] for item in filtered}
                for fallback in fallback_items:
                    if len(filtered) >= 3:
                        break
                    if fallback["titulo"] in selected_titles:
                        continue
                    filtered.append(fallback)
                    selected_titles.add(fallback["titulo"])

                return filtered[:3]

        return fallback_items[:3]

    def _fallback_recommendations(
        self, books: list[dict[str, Any]], categories: list[dict[str, Any]]
    ) -> list[BookRecommendation]:
        if not books:
            return [
                BookRecommendation(
                    titulo="Sem novos livros no momento",
                    motivo="Nao ha titulos ineditos disponiveis agora. Reavalie apos novas entradas no catalogo.",
                )
            ]

        favorite_categories = [item["categoria"] for item in categories]

        scored = []
        for book in books:
            score = 0
            if book.get("disponivel"):
                score += 3
            if favorite_categories and book.get("categoria") == favorite_categories[0]:
                score += 3
            elif book.get("categoria") in favorite_categories:
                score += 2
            pages = book.get("total_paginas") or 120
            if 80 <= pages <= 260:
                score += 1
            scored.append((score, book))

        scored.sort(key=lambda item: (item[0], item[1].get("disponivel", 0)), reverse=True)

        recommendations: list[BookRecommendation] = []
        for _, book in scored[:3]:
            categoria = book.get("categoria") or "temas diversos"
            motivo = (
                f"Combina com interesse em {categoria} e ajuda a manter evolucao de leitura com nivel adequado."
            )
            recommendations.append(
                BookRecommendation(
                    titulo=book["titulo"],
                    motivo=motivo,
                )
            )

        return recommendations
