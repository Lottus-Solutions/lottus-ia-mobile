from pydantic import BaseModel


class BookRecommendation(BaseModel):
    titulo: str
    motivo: str

    def to_dict(self) -> dict:
        return self.model_dump()
