from datetime import date
from typing import Any

from repositories.db import Database


class StudentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_student(self, aluno_id: int) -> dict[str, Any] | None:
        query = """
            SELECT a.id,
                   a.matricula,
                   a.nome,
                   a.qtd_bonus,
                   a.qtd_livros_lidos,
                   t.serie
            FROM alunos a
            LEFT JOIN turmas t ON t.id = a.turma_id
            WHERE a.id = %s
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            return cursor.fetchone()

    def get_reading_history(self, aluno_id: int) -> list[dict[str, Any]]:
        query = """
            SELECT e.id,
                   e.livro_id,
                   e.data_emprestimo,
                   e.data_devolucao_prevista,
                   e.data_devolucao_efetiva,
                   e.dias_atrasados,
                   e.status_emprestimo,
                   l.titulo,
                   l.categoria,
                   l.total_paginas
            FROM emprestimos e
            INNER JOIN livros l ON l.id = e.livro_id
            WHERE e.aluno_id = %s
            ORDER BY e.data_emprestimo DESC
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            return cursor.fetchall() or []

    def get_category_preferences(self, aluno_id: int) -> list[dict[str, Any]]:
        query = """
            SELECT l.categoria,
                   COUNT(*) AS quantidade
            FROM emprestimos e
            INNER JOIN livros l ON l.id = e.livro_id
            WHERE e.aluno_id = %s
              AND l.categoria IS NOT NULL
            GROUP BY l.categoria
            ORDER BY quantidade DESC
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            return cursor.fetchall() or []

    def get_reading_frequency_by_month(self, aluno_id: int) -> list[dict[str, Any]]:
        query = """
            SELECT DATE_FORMAT(e.data_emprestimo, '%Y-%m') AS ano_mes,
                   COUNT(*) AS total_emprestimos
            FROM emprestimos e
            WHERE e.aluno_id = %s
            GROUP BY DATE_FORMAT(e.data_emprestimo, '%Y-%m')
            ORDER BY ano_mes DESC
            LIMIT 6
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            return cursor.fetchall() or []

    def get_delay_stats(self, aluno_id: int) -> dict[str, Any]:
        query = """
            SELECT COALESCE(SUM(CASE WHEN dias_atrasados > 0 THEN 1 ELSE 0 END), 0) AS devolucoes_com_atraso,
                   COALESCE(AVG(dias_atrasados), 0) AS media_dias_atraso,
                   COALESCE(MAX(dias_atrasados), 0) AS max_dias_atraso
            FROM emprestimos
            WHERE aluno_id = %s
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            return cursor.fetchone() or {}

    def build_profile_input(self, aluno_id: int) -> dict[str, Any] | None:
        student = self.get_student(aluno_id)
        if not student:
            return None

        history = self.get_reading_history(aluno_id)
        categories = self.get_category_preferences(aluno_id)
        frequency = self.get_reading_frequency_by_month(aluno_id)
        delays = self.get_delay_stats(aluno_id)

        devolvidos = sum(1 for item in history if item["status_emprestimo"] == "DEVOLVIDO")
        ativos = sum(1 for item in history if item["status_emprestimo"] == "ATIVO")

        return {
            "aluno": student,
            "emprestimos": history,
            "categorias_favoritas": categories,
            "frequencia_mensal": frequency,
            "indicadores": {
                "total_emprestimos": len(history),
                "emprestimos_devolvidos": devolvidos,
                "emprestimos_ativos": ativos,
                "devolucoes_com_atraso": int(delays.get("devolucoes_com_atraso", 0) or 0),
                "media_dias_atraso": float(delays.get("media_dias_atraso", 0) or 0),
                "max_dias_atraso": int(delays.get("max_dias_atraso", 0) or 0),
            },
            "gerado_em": date.today().isoformat(),
        }
