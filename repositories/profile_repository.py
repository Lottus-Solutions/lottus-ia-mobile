import ast
import json
from datetime import datetime
from typing import Any, Sequence

from repositories.db import Database


class ProfileRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def ensure_table(self) -> None:
        query = """
            CREATE TABLE IF NOT EXISTS perfil_leitura (
                id BIGINT NOT NULL AUTO_INCREMENT,
                aluno_id BIGINT NOT NULL,
                perfil_texto TEXT NOT NULL,
                embedding LONGTEXT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uk_perfil_aluno (aluno_id),
                CONSTRAINT fk_perfil_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        with self.db.cursor(dictionary=False) as cursor:
            cursor.execute(query)
            for alter_query in (
                "ALTER TABLE perfil_leitura MODIFY COLUMN perfil_texto TEXT NOT NULL",
                "ALTER TABLE perfil_leitura ADD COLUMN embedding LONGTEXT NULL",
                "ALTER TABLE perfil_leitura ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            ):
                try:
                    cursor.execute(alter_query)
                except Exception:
                    continue

    def upsert_profile(
        self,
        aluno_id: int,
        perfil_texto: str,
        embedding: Sequence[float] | None = None,
    ) -> None:
        embedding_text = json.dumps([float(value) for value in embedding]) if embedding else None
        query = """
            INSERT INTO perfil_leitura (aluno_id, perfil_texto, embedding)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                perfil_texto = VALUES(perfil_texto),
                embedding = VALUES(embedding),
                updated_at = CURRENT_TIMESTAMP
        """
        with self.db.cursor(dictionary=False) as cursor:
            cursor.execute(query, (aluno_id, perfil_texto, embedding_text))

    def get_profile(self, aluno_id: int) -> dict | None:
        query = """
            SELECT id, aluno_id, perfil_texto, embedding, updated_at AS atualizado_em
            FROM perfil_leitura
            WHERE aluno_id = %s
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            profile = cursor.fetchone()
            if not profile:
                return None

            profile["embedding"] = self._deserialize_embedding(profile.get("embedding"))
            atualizado_em = profile.get("atualizado_em")
            profile["atualizado_em"] = (
                atualizado_em.isoformat() if isinstance(atualizado_em, datetime) else atualizado_em
            )
            return profile

    @staticmethod
    def _deserialize_embedding(raw_embedding: Any) -> list[float] | None:
        if raw_embedding in (None, ""):
            return None

        if isinstance(raw_embedding, (list, tuple)):
            return [float(value) for value in raw_embedding]

        if isinstance(raw_embedding, bytes):
            raw_embedding = raw_embedding.decode("utf-8")

        if isinstance(raw_embedding, str):
            try:
                parsed = json.loads(raw_embedding)
                if isinstance(parsed, list):
                    return [float(value) for value in parsed]
            except json.JSONDecodeError:
                pass

            try:
                parsed = ast.literal_eval(raw_embedding)
                if isinstance(parsed, (list, tuple)):
                    return [float(value) for value in parsed]
            except (ValueError, SyntaxError):
                return None

        return None
