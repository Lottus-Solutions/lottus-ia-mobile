import ast
import json
import logging
from functools import lru_cache
from math import sqrt
from time import perf_counter
from typing import Any, Sequence

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - dependency is provided in requirements
    SentenceTransformer = None


logger = logging.getLogger(__name__)
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _get_database(db: Any | None = None) -> Any:
    if db is not None:
        return db

    from app.config import Settings
    from repositories.db import Database

    settings = Settings.from_env()
    return Database(settings)


@lru_cache(maxsize=1)
def _get_embedding_model() -> Any:
    if SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers nao esta instalado. Execute `pip install sentence-transformers`."
        )

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def gerar_embedding_texto(texto: str) -> list[float]:
    texto_limpo = (texto or "").strip()
    if not texto_limpo:
        return []

    modelo = _get_embedding_model()
    vetor = modelo.encode(texto_limpo, convert_to_numpy=True, normalize_embeddings=False)
    if hasattr(vetor, "tolist"):
        vetor = vetor.tolist()

    return [float(valor) for valor in vetor]


def cosine_similarity(vec1: Sequence[float], vec2: Sequence[float]) -> float:
    if not vec1 or not vec2:
        return 0.0

    limite = min(len(vec1), len(vec2))
    produto = 0.0
    norma1 = 0.0
    norma2 = 0.0

    for indice in range(limite):
        valor1 = float(vec1[indice])
        valor2 = float(vec2[indice])
        produto += valor1 * valor2
        norma1 += valor1 * valor1
        norma2 += valor2 * valor2

    if norma1 == 0.0 or norma2 == 0.0:
        return 0.0

    return produto / (sqrt(norma1) * sqrt(norma2))


def salvar_perfil_leitura(
    usuario_id: int,
    perfil_texto: str,
    embedding: Sequence[float] | None,
    db: Any | None = None,
) -> None:
    database = _get_database(db)
    embedding_text = json.dumps([float(valor) for valor in embedding]) if embedding else None

    query = """
        INSERT INTO perfil_leitura (aluno_id, perfil_texto, embedding)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            perfil_texto = VALUES(perfil_texto),
            embedding = VALUES(embedding),
            updated_at = CURRENT_TIMESTAMP
    """

    with database.cursor(dictionary=False) as cursor:
        cursor.execute(query, (usuario_id, perfil_texto, embedding_text))

    logger.info("[OK] Perfil atualizado")
    logger.info("[OK] Embedding salvo em perfil_leitura")


def buscar_top_livros_por_perfil(
    perfil_texto: str,
    top_k: int = 10,
    livros: list[dict[str, Any]] | None = None,
    db: Any | None = None,
) -> list[dict[str, Any]]:
    perfil_embedding = gerar_embedding_texto(perfil_texto)
    if not perfil_embedding:
        return []

    return buscar_top_livros_por_embedding(
        perfil_embedding,
        top_k=top_k,
        livros=livros,
        db=db,
    )


def buscar_top_livros_por_embedding(
    perfil_embedding: Sequence[float],
    top_k: int = 10,
    livros: list[dict[str, Any]] | None = None,
    db: Any | None = None,
) -> list[dict[str, Any]]:
    start_time = perf_counter()
    if livros is None:
        database = _get_database(db)
        candidatos = _carregar_livros_vetorizados(database)
    else:
        candidatos = livros

    pontuados: list[tuple[float, dict[str, Any]]] = []
    livros_comparados = 0

    for livro in candidatos:
        embedding_bruto = livro.get("embedding")
        embedding_livro = _parse_embedding(embedding_bruto)
        if not embedding_livro:
            continue

        livros_comparados += 1
        similaridade = cosine_similarity(perfil_embedding, embedding_livro)
        livro_limpo = {chave: valor for chave, valor in livro.items() if chave != "embedding"}
        livro_limpo["similaridade"] = round(similaridade, 6)
        pontuados.append((similaridade, livro_limpo))

    pontuados.sort(key=lambda item: item[0], reverse=True)
    top_livros = [item[1] for item in pontuados[: max(top_k, 0)]]

    elapsed_seconds = perf_counter() - start_time
    logger.info("[OK] %s livros comparados", livros_comparados)
    logger.info("[OK] Top %s encontrados em %.1fs", len(top_livros), elapsed_seconds)
    logger.info("[OK] Prompt reduzido para apenas %s livros", len(top_livros))

    return top_livros


def _carregar_livros_vetorizados(database: Any) -> list[dict[str, Any]]:
    query = """
        SELECT l.id,
               l.titulo,
               l.autor,
               l.categoria,
               l.total_paginas,
               l.embedding
        FROM livros l
        WHERE l.embedding IS NOT NULL
          AND l.embedding <> ''
    """

    with database.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall() or []


def _parse_embedding(raw_embedding: Any) -> list[float] | None:
    if raw_embedding in (None, ""):
        return None

    if isinstance(raw_embedding, (list, tuple)):
        return [float(valor) for valor in raw_embedding]

    if isinstance(raw_embedding, bytes):
        raw_embedding = raw_embedding.decode("utf-8")

    if isinstance(raw_embedding, str):
        try:
            parsed = json.loads(raw_embedding)
            if isinstance(parsed, list):
                return [float(valor) for valor in parsed]
        except json.JSONDecodeError:
            pass

        try:
            parsed = ast.literal_eval(raw_embedding)
            if isinstance(parsed, (list, tuple)):
                return [float(valor) for valor in parsed]
        except (ValueError, SyntaxError):
            return None

        numeros = [parte.strip() for parte in raw_embedding.split(",") if parte.strip()]
        if numeros:
            try:
                return [float(parte) for parte in numeros]
            except ValueError:
                return None

    return None