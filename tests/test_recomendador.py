import json

import recomendador


class FakeModel:
    def encode(self, texto, convert_to_numpy=True, normalize_embeddings=False):
        return [1.0, 2.0, 3.0] if "estrategico" in texto else [0.5, 0.5, 0.5]


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.rows = []

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if "FROM livros" in query:
            self.rows = [
                {
                    "id": 1,
                    "titulo": "Livro A",
                    "autor": "Autor A",
                    "categoria": "Fantasia",
                    "total_paginas": 100,
                    "embedding": json.dumps([1.0, 2.0, 3.0]),
                },
                {
                    "id": 2,
                    "titulo": "Livro B",
                    "autor": "Autor B",
                    "categoria": "Tecnico",
                    "total_paginas": 120,
                    "embedding": json.dumps([0.0, 0.0, 1.0]),
                },
            ]

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeDatabase:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self, dictionary=True):
        return self.cursor_instance


def test_gerar_embedding_texto_usa_modelo_fake(monkeypatch):
    monkeypatch.setattr(recomendador, "SentenceTransformer", lambda *_args, **_kwargs: FakeModel())
    recomendador._get_embedding_model.cache_clear()

    embedding = recomendador.gerar_embedding_texto("Leitor estrategico")

    assert embedding == [1.0, 2.0, 3.0]


def test_buscar_top_livros_por_embedding_ordena_por_similaridade():
    livros = [
        {"id": 1, "titulo": "Livro A", "embedding": json.dumps([1.0, 2.0, 3.0])},
        {"id": 2, "titulo": "Livro B", "embedding": json.dumps([0.0, 0.0, 1.0])},
    ]

    top_livros = recomendador.buscar_top_livros_por_embedding([1.0, 2.0, 3.0], livros=livros)

    assert [livro["id"] for livro in top_livros] == [1, 2]
    assert top_livros[0]["similaridade"] > top_livros[1]["similaridade"]


def test_salvar_perfil_leitura_persiste_embedding():
    fake_db = FakeDatabase()

    recomendador.salvar_perfil_leitura(7, "Perfil sintetico", [0.1, 0.2, 0.3], db=fake_db)

    query, params = fake_db.cursor_instance.executed[0]
    assert "INSERT INTO perfil_leitura" in query
    assert params[0] == 7
    assert params[1] == "Perfil sintetico"
    assert params[2] == json.dumps([0.1, 0.2, 0.3])