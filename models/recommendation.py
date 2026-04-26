from dataclasses import asdict, dataclass


@dataclass(slots=True)
class BookRecommendation:
    titulo: str
    motivo: str

    def to_dict(self) -> dict:
        return asdict(self)
