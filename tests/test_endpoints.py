from types import SimpleNamespace
import io

import pytest

from app import create_app


class FakeProfileAgent:
    def generate_profile(self, aluno_id: int) -> dict:
        return {"aluno_id": aluno_id, "perfil_texto": "Perfil sintetico"}


class FakeRecommendationAgent:
    def recommend(self, aluno_id: int) -> list[dict]:
        return [
            {"titulo": "Livro A", "motivo": "Aderente ao perfil"},
            {"titulo": "Livro B", "motivo": "Expande repertorio"},
            {"titulo": "Livro C", "motivo": "Progressao de dificuldade"},
        ]


class FakeChatAgent:
    def respond(self, aluno_id, texto=None, audio_bytes=None, mime_type="audio/mpeg") -> dict:
        entrada = texto or ("transcricao" if audio_bytes else "")
        return {
            "aluno_id": aluno_id,
            "entrada_processada": entrada,
            "transcricao": None,
            "resposta": "Plano semanal de leitura aplicado.",
        }


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "repositories.profile_repository.ProfileRepository.ensure_table",
        lambda self: None,
    )

    app = create_app()

    monkeypatch.setattr(
        "routes.ai_routes._build_dependencies",
        lambda: {
            "profile_agent": FakeProfileAgent(),
            "recommendation_agent": FakeRecommendationAgent(),
            "chat_agent": FakeChatAgent(),
        },
    )

    return app.test_client()


def test_perfil_leitura_ok(client):
    response = client.post("/perfil-leitura", json={"aluno_id": 1})
    assert response.status_code == 200
    data = response.get_json()
    assert data["aluno_id"] == 1
    assert "perfil_texto" in data


def test_recomendar_ok(client):
    response = client.post("/recomendar", json={"aluno_id": 1})
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["recomendacoes"]) == 3


def test_chat_reforco_ok(client):
    response = client.post(
        "/chat-reforco",
        data={"aluno_id": "1", "texto": "Meu filho tem dificuldade de interpretacao"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["aluno_id"] == 1
    assert "resposta" in data


def test_chat_reforco_sem_aluno_id(client):
    response = client.post(
        "/chat-reforco",
        data={"texto": "Meu filho tem dificuldade de interpretacao"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "aluno_id deve ser inteiro"


def test_chat_reforco_audio_ok(client):
    response = client.post(
        "/chat-reforco",
        data={
            "aluno_id": "1",
            "audio": (io.BytesIO(b"fake-audio"), "audio.mp3"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["aluno_id"] == 1
    assert data["entrada_processada"] == "transcricao"
