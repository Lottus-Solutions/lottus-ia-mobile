from datetime import datetime

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
                atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uk_perfil_aluno (aluno_id),
                CONSTRAINT fk_perfil_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        alter_query = """
            ALTER TABLE perfil_leitura
            MODIFY COLUMN perfil_texto TEXT NOT NULL
        """
        with self.db.cursor(dictionary=False) as cursor:
            cursor.execute(query)
            # Garantimos compatibilidade com bancos ja existentes que ainda estao em VARCHAR(600).
            cursor.execute(alter_query)

    def upsert_profile(self, aluno_id: int, perfil_texto: str) -> None:
        query = """
            INSERT INTO perfil_leitura (aluno_id, perfil_texto)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                perfil_texto = VALUES(perfil_texto),
                atualizado_em = CURRENT_TIMESTAMP
        """
        with self.db.cursor(dictionary=False) as cursor:
            cursor.execute(query, (aluno_id, perfil_texto))

    def get_profile(self, aluno_id: int) -> dict | None:
        query = """
            SELECT id, aluno_id, perfil_texto, atualizado_em
            FROM perfil_leitura
            WHERE aluno_id = %s
        """
        with self.db.cursor() as cursor:
            cursor.execute(query, (aluno_id,))
            profile = cursor.fetchone()
            if not profile:
                return None

            atualizado_em = profile.get("atualizado_em")
            profile["atualizado_em"] = (
                atualizado_em.isoformat() if isinstance(atualizado_em, datetime) else atualizado_em
            )
            return profile
