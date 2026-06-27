from pydantic import BaseModel


class GenreResponseSchema(BaseModel):
    id: int
    name: str
    movies_count: int

    model_config = {
        "from_attributes": True,
    }
