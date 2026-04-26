from typing import Any

from repositories.db import Database


class BookRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_unread_books(
        self,
        aluno_id: int,
        preferred_categories: list[str] | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        top_categories = [cat for cat in (preferred_categories or []) if cat][:3]

        category_score_clauses: list[str] = []
        category_params: list[Any] = []
        for idx, category in enumerate(top_categories):
            score = 3 - idx
            category_score_clauses.append(f"WHEN l.categoria = %s THEN {score}")
            category_params.append(category)

        category_score_expr = "0"
        if category_score_clauses:
            category_score_expr = "CASE " + " ".join(category_score_clauses) + " ELSE 0 END"

        query = """
            SELECT l.id,
                   l.titulo,
                   l.autor,
                   l.categoria,
                   l.total_paginas,
                   CASE
                     WHEN EXISTS (
                         SELECT 1
                         FROM emprestimos e2
                         WHERE e2.livro_id = l.id
                           AND e2.status_emprestimo = 'ATIVO'
                     ) THEN 0
                     ELSE 1
                   END AS disponivel,
                   {category_score} AS categoria_score,
                   CASE WHEN l.total_paginas BETWEEN 80 AND 260 THEN 1 ELSE 0 END AS faixa_paginas_score
            FROM livros l
            WHERE NOT EXISTS (
                SELECT 1
                FROM emprestimos e
                WHERE e.aluno_id = %s
                  AND e.livro_id = l.id
            )
            ORDER BY categoria_score DESC, disponivel DESC, faixa_paginas_score DESC, l.titulo ASC
            LIMIT %s
        """.format(category_score=category_score_expr)

        params = [*category_params, aluno_id, int(limit)]
        with self.db.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall() or []
