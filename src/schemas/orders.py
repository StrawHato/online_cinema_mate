from pydantic import BaseModel


class OrderMovieResponseSchema(BaseModel):
    uuid: str
    name: str
    year: int

    model_config = {
        "from_attributes": True,
    }
