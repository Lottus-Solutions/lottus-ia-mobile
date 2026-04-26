from flask import Flask, jsonify, render_template_string


OPENAPI_SPEC: dict = {
    "openapi": "3.0.3",
    "info": {
        "title": "Lottus AI API",
        "version": "1.0.0",
        "description": "API de agentes de IA para biblioteca escolar.",
    },
    "servers": [{"url": "http://localhost:5000"}],
    "paths": {
        "/health": {
            "get": {
                "summary": "Healthcheck da API",
                "responses": {
                    "200": {
                        "description": "API ativa",
                        "content": {
                            "application/json": {
                                "example": {"status": "ok", "service": "lottus-ai-api"}
                            }
                        },
                    }
                },
            }
        },
        "/perfil-leitura": {
            "post": {
                "summary": "Gera e salva perfil de leitura",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["aluno_id"],
                                "properties": {
                                    "aluno_id": {"type": "integer", "example": 1}
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Perfil gerado",
                        "content": {
                            "application/json": {
                                "example": {
                                    "aluno_id": 1,
                                    "perfil_texto": "Aluno com boa frequencia e preferencia por aventura.",
                                }
                            }
                        },
                    },
                    "400": {"description": "Entrada invalida"},
                    "404": {"description": "Aluno nao encontrado"},
                },
            }
        },
        "/recomendar": {
            "post": {
                "summary": "Retorna 3 recomendacoes de livros",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["aluno_id"],
                                "properties": {
                                    "aluno_id": {"type": "integer", "example": 1}
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Recomendacoes retornadas",
                        "content": {
                            "application/json": {
                                "example": {
                                    "aluno_id": 1,
                                    "recomendacoes": [
                                        {
                                            "titulo": "A Volta ao Mundo em 80 Dias",
                                            "motivo": "Combina com interesse em aventura.",
                                        },
                                        {
                                            "titulo": "Dom Casmurro",
                                            "motivo": "Expande repertorio de leitura.",
                                        },
                                        {
                                            "titulo": "Capitaes da Areia",
                                            "motivo": "Progressao de complexidade textual.",
                                        },
                                    ],
                                }
                            }
                        },
                    },
                    "400": {"description": "Entrada invalida"},
                    "404": {"description": "Aluno nao encontrado"},
                },
            }
        },
        "/chat-reforco": {
            "post": {
                "summary": "Chat de reforco escolar via texto ou audio",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["aluno_id"],
                                "properties": {
                                    "aluno_id": {"type": "integer", "example": 1},
                                    "texto": {
                                        "type": "string",
                                        "example": "Meu filho esta mal em matematica",
                                    },
                                },
                                "description": "Enviar aluno_id e ao menos um dos campos: texto ou audio.",
                            }
                        },
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "required": ["aluno_id"],
                                "properties": {
                                    "aluno_id": {"type": "integer", "example": 1},
                                    "texto": {
                                        "type": "string",
                                        "example": "Meu filho esta mal em matematica",
                                    },
                                    "audio": {
                                        "type": "string",
                                        "format": "binary",
                                    },
                                },
                                "description": "Enviar aluno_id e ao menos um dos campos: texto ou audio.",
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Resposta pedagógica gerada",
                        "content": {
                            "application/json": {
                                "example": {
                                    "aluno_id": 1,
                                    "entrada_processada": "Meu filho esta mal em matematica",
                                    "transcricao": None,
                                    "resposta": "Plano semanal de leitura guiada com acompanhamento dos pais.",
                                }
                            }
                        },
                    },
                    "400": {"description": "Entrada invalida"},
                },
            }
        },
    },
}


SWAGGER_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Lottus AI API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #f7f7f8; }
      #swagger-ui { max-width: 1100px; margin: 0 auto; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = function () {
        window.ui = SwaggerUIBundle({
          url: '/openapi.json',
          dom_id: '#swagger-ui',
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: 'BaseLayout'
        });
      };
    </script>
  </body>
</html>
"""


def register_swagger(app: Flask) -> None:
    @app.get("/openapi.json")
    def openapi_spec():
        return jsonify(OPENAPI_SPEC)

    @app.get("/docs")
    def swagger_docs():
        return render_template_string(SWAGGER_HTML)
