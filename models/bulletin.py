from pydantic import BaseModel, Field


class DisciplinaPrioritaria(BaseModel):
    disciplina: str = Field(description="Nome da disciplina em dificuldade")
    desafio: str = Field(description="Desafio especifico do aluno nessa disciplina")
    estrategia_leitura: str = Field(
        description="Estrategia de leitura conectada a disciplina"
    )
    acao_semana: str = Field(description="Acao concreta para realizar na semana")


class DiaPlanoLeitura(BaseModel):
    dia: str = Field(description="Dia da semana, ex: Segunda-feira")
    tempo: str = Field(description="Tempo recomendado de leitura, ex: 20 minutos")
    leitura: str = Field(description="Tipo ou tema de leitura recomendado para o dia")


class PlanoAcao(BaseModel):
    diagnostico_geral: str = Field(
        description="Avaliacao breve do desempenho geral do aluno com base na media e nas disciplinas"
    )
    disciplinas_prioritarias: list[DisciplinaPrioritaria] = Field(
        description="Ate 3 disciplinas prioritarias com desafio, estrategia de leitura e acao da semana"
    )
    plano_semanal_leitura: list[DiaPlanoLeitura] = Field(
        description="Rotina de 5 dias com tempo e tipo de leitura recomendados"
    )
    como_pais_podem_ajudar: list[str] = Field(
        description="Orientacoes simples para os pais acompanharem sem pressao"
    )
    meta_30_dias: str = Field(
        description="Objetivo claro e mensuravel para o aluno alcancar em 30 dias"
    )

    def to_dict(self) -> dict:
        return self.model_dump()
