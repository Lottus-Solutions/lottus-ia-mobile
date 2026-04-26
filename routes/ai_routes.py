from flask import Blueprint, current_app, jsonify, request

from agents.profile_agent import ProfileAgent
from agents.recommendation_agent import RecommendationAgent
from agents.reinforcement_chat_agent import ReinforcementChatAgent
from repositories.book_repository import BookRepository
from repositories.profile_repository import ProfileRepository
from repositories.student_repository import StudentRepository
from services.gemini_service import GeminiService


ai_blueprint = Blueprint("ai", __name__)


def _build_dependencies() -> dict:
    settings = current_app.config["SETTINGS"]
    db = current_app.config["DB"]

    student_repository = StudentRepository(db)
    profile_repository = ProfileRepository(db)
    book_repository = BookRepository(db)
    gemini_service = GeminiService(settings)

    return {
        "profile_agent": ProfileAgent(student_repository, profile_repository, gemini_service),
        "recommendation_agent": RecommendationAgent(
            student_repository,
            profile_repository,
            book_repository,
            gemini_service,
        ),
        "chat_agent": ReinforcementChatAgent(
            gemini_service,
            student_repository,
            profile_repository,
        ),
    }


@ai_blueprint.post("/perfil-leitura")
def perfil_leitura():
    body = request.get_json(silent=True) or {}
    aluno_id = body.get("aluno_id")

    if not isinstance(aluno_id, int):
        return jsonify({"error": "aluno_id deve ser inteiro"}), 400

    dependencies = _build_dependencies()
    try:
        result = dependencies["profile_agent"].generate_profile(aluno_id)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"falha interna: {exc}"}), 500


@ai_blueprint.post("/recomendar")
def recomendar():
    body = request.get_json(silent=True) or {}
    aluno_id = body.get("aluno_id")

    if not isinstance(aluno_id, int):
        return jsonify({"error": "aluno_id deve ser inteiro"}), 400

    dependencies = _build_dependencies()
    try:
        recommendations = dependencies["recommendation_agent"].recommend(aluno_id)
        return jsonify({"aluno_id": aluno_id, "recomendacoes": recommendations}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"falha interna: {exc}"}), 500


@ai_blueprint.post("/chat-reforco")
def chat_reforco():
    body = request.get_json(silent=True) or {}
    aluno_id_raw = request.form.get("aluno_id", body.get("aluno_id"))
    texto = request.form.get("texto")
    if texto is None:
        texto = body.get("texto")

    if aluno_id_raw is None:
        return jsonify({"error": "aluno_id deve ser inteiro"}), 400

    try:
        aluno_id = int(aluno_id_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "aluno_id deve ser inteiro"}), 400

    audio_file = request.files.get("audio")

    audio_bytes = None
    mime_type = "audio/mpeg"
    if audio_file:
        audio_bytes = audio_file.read()
        mime_type = audio_file.mimetype or mime_type

    dependencies = _build_dependencies()

    try:
        response = dependencies["chat_agent"].respond(
            aluno_id=aluno_id,
            texto=texto,
            audio_bytes=audio_bytes,
            mime_type=mime_type,
        )
        return jsonify(response), 200
    except ValueError as exc:
        status_code = 404 if str(exc) == "Aluno nao encontrado" else 400
        return jsonify({"error": str(exc)}), status_code
    except Exception as exc:
        return jsonify({"error": f"falha interna: {exc}"}), 500
