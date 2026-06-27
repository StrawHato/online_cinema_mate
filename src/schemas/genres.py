from pydantic import BaseModel


class GenreCreateRequestSchema(BaseModel):
    name: str


class GenreUpdateRequestSchema(BaseModel):
    name: str | None = None


class GenreResponseSchema(BaseModel):
    id: int
    name: str
    movies_count: int

    model_config = {
        "from_attributes": True,
    }


class GenreDetailResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }
