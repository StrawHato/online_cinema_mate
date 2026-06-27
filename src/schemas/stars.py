from pydantic import BaseModel


class StarCreateRequestSchema(BaseModel):
    name: str


class StarUpdateRequestSchema(BaseModel):
    name: str | None = None


class StarResponseSchema(BaseModel):
    id: int
    name: str
    movies_count: int

    model_config = {
        "from_attributes": True,
    }


class StarDetailResponseSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
    }
