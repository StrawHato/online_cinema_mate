from decimal import Decimal

import pytest
from sqlalchemy import select

from src.database.models import (
    MovieModel,
    GenreModel,
    DirectorModel,
    StarModel,
    CertificationModel,
)

MOVIES_URL = "/api/v1/movies/"


def movie_data(
    name: str = "Interstellar",
    year: int = 2014,
):
    return {
        "name": name,
        "year": year,
        "time": 169,
        "imdb": "8.7",
        "votes": 2200000,
        "meta_score": 74,
        "gross": "773.00",
        "description": "Best sci-fi movie",
        "price": "12.99",
        "certification": "PG-13",
        "genres": [
            "Adventure",
            "Drama",
            "Sci-Fi",
        ],
        "stars": [
            "Matthew McConaughey",
            "Anne Hathaway",
        ],
        "directors": [
            "Christopher Nolan",
        ],
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_success(
    admin_client,
    db_session,
):
    response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Interstellar"
    assert body["year"] == 2014
    assert body["time"] == 169
    assert body["price"] == "12.99"

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.name == "Interstellar",
        )
    )

    assert movie is not None
    assert movie.description == "Best sci-fi movie"
    assert movie.imdb == Decimal("8.7")
    assert movie.price == Decimal("12.99")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_creates_related_entities(
    admin_client,
    db_session,
):
    response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    assert response.status_code == 201

    certification = await db_session.scalar(
        select(CertificationModel).where(
            CertificationModel.name == "PG-13"
        )
    )

    assert certification is not None

    genre = await db_session.scalar(
        select(GenreModel).where(
            GenreModel.name == "Sci-Fi"
        )
    )

    assert genre is not None

    director = await db_session.scalar(
        select(DirectorModel).where(
            DirectorModel.name == "Christopher Nolan"
        )
    )

    assert director is not None

    star = await db_session.scalar(
        select(StarModel).where(
            StarModel.name == "Matthew McConaughey"
        )
    )

    assert star is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_duplicate(
    admin_client,
):
    await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Movie already exists."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_movie_success(
    admin_client,
    client,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create_response.json()["uuid"]

    response = await client.get(
        f"{MOVIES_URL}{movie_uuid}/"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["uuid"] == movie_uuid
    assert body["name"] == "Interstellar"
    assert body["certification"]["name"] == "PG-13"

    assert len(body["genres"]) == 3
    assert len(body["stars"]) == 2
    assert len(body["directors"]) == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_movie_not_found(
    client,
):
    response = await client.get(
        f"{MOVIES_URL}unknown-uuid/"
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_movies_empty(
    client,
):
    response = await client.get(MOVIES_URL)

    assert response.status_code == 200

    body = response.json()

    assert body["items"] == []
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total"] == 0
    assert body["total_pages"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_movies_success(
    admin_client,
    client,
):
    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Interstellar",
        ),
    )

    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Oppenheimer",
            year=2023,
        ),
    )

    response = await client.get(MOVIES_URL)

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_movies_by_name(
    admin_client,
    client,
):
    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Interstellar",
        ),
    )

    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Oppenheimer",
        ),
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "search": "Inter",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert body["items"][0]["name"] == "Interstellar"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_by_year(
    admin_client,
    client,
):
    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Movie 2014",
            year=2014,
        ),
    )

    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Movie 2023",
            year=2023,
        ),
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "year": 2023,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["year"] == 2023


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_by_genre(
    admin_client,
    client,
):
    movie = movie_data(
        name="Drama Movie",
    )
    movie["genres"] = [
        "Drama",
    ]

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    movie = movie_data(
        name="Comedy Movie",
    )
    movie["genres"] = [
        "Comedy",
    ]

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "genre": "Drama",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["name"] == "Drama Movie"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_by_director(
    admin_client,
    client,
):
    movie = movie_data(
        name="Movie A",
    )
    movie["directors"] = [
        "Christopher Nolan",
    ]

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    movie = movie_data(
        name="Movie B",
    )
    movie["directors"] = [
        "James Cameron",
    ]

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "director": "Christopher Nolan",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["name"] == "Movie A"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_by_star(
    admin_client,
    client,
):
    movie = movie_data(
        name="Interstellar",
    )
    movie["stars"] = [
        "Matthew McConaughey",
    ]

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    movie = movie_data(
        name="Titanic",
    )
    movie["stars"] = [
        "Leonardo DiCaprio",
    ]

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "star": "Matthew McConaughey",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["name"] == "Interstellar"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_by_imdb_min(
    admin_client,
    client,
):
    movie = movie_data(
        name="Movie 1",
    )
    movie["imdb"] = "7.1"

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    movie = movie_data(
        name="Movie 2",
    )
    movie["imdb"] = "9.4"

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "imdb_min": 9,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["name"] == "Movie 2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_by_imdb_max(
    admin_client,
    client,
):
    movie = movie_data(
        name="Movie 1",
    )
    movie["imdb"] = "6.5"

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    movie = movie_data(
        name="Movie 2",
    )
    movie["imdb"] = "9.1"

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "imdb_max": 7,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["name"] == "Movie 1"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sort_movies_by_name(
    admin_client,
    client,
):
    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Z Movie",
        ),
    )

    await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="A Movie",
        ),
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "sort": "name",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert items[0]["name"] == "A Movie"
    assert items[1]["name"] == "Z Movie"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sort_movies_by_price_desc(
    admin_client,
    client,
):
    movie = movie_data(
        name="Cheap",
    )
    movie["price"] = "5.00"

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    movie = movie_data(
        name="Expensive",
    )
    movie["price"] = "25.00"

    await admin_client.post(
        MOVIES_URL,
        json=movie,
    )

    response = await client.get(
        MOVIES_URL,
        params={
            "sort": "-price",
        },
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert items[0]["name"] == "Expensive"
    assert items[1]["name"] == "Cheap"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_movies_pagination(
    admin_client,
    client,
):
    for i in range(25):
        await admin_client.post(
            MOVIES_URL,
            json=movie_data(
                name=f"Movie {i}",
            ),
        )

    response = await client.get(
        MOVIES_URL,
        params={
            "page": 2,
            "page_size": 10,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["page"] == 2
    assert body["page_size"] == 10
    assert body["total"] == 25
    assert len(body["items"]) == 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_success(
    admin_client,
    db_session,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create_response.json()["uuid"]

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == movie_uuid
        )
    )

    payload = movie_data(
        name="Oppenheimer",
        year=2023,
    )

    payload["price"] = "15.99"
    payload["imdb"] = "8.5"
    payload["certification"] = "R"
    payload["genres"] = [
        "Biography",
        "Drama",
    ]
    payload["directors"] = [
        "Christopher Nolan",
    ]
    payload["stars"] = [
        "Cillian Murphy",
        "Emily Blunt",
    ]

    response = await admin_client.patch(
        f"{MOVIES_URL}{movie.id}/",
        json=payload,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Oppenheimer"
    assert body["year"] == 2023
    assert body["price"] == "15.99"
    assert body["imdb"] == "8.5"
    assert body["certification"]["name"] == "R"

    genres = {
        genre["name"]
        for genre in body["genres"]
    }

    assert genres == {
        "Biography",
        "Drama",
    }

    stars = {
        star["name"]
        for star in body["stars"]
    }

    assert stars == {
        "Cillian Murphy",
        "Emily Blunt",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_not_found(
    admin_client,
):
    response = await admin_client.patch(
        f"{MOVIES_URL}999999/",
        json=movie_data(),
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Movie not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_changes_certification(
    admin_client,
    db_session,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create_response.json()["uuid"]
        )
    )

    payload = movie_data()
    payload["certification"] = "NC-17"

    response = await admin_client.patch(
        f"{MOVIES_URL}{movie.id}/",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json()["certification"]["name"] == "NC-17"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_changes_genres(
    admin_client,
    db_session,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create_response.json()["uuid"]
        )
    )

    payload = movie_data()
    payload["genres"] = [
        "Action",
        "Thriller",
    ]

    response = await admin_client.patch(
        f"{MOVIES_URL}{movie.id}/",
        json=payload,
    )

    assert response.status_code == 200

    genres = {
        genre["name"]
        for genre in response.json()["genres"]
    }

    assert genres == {
        "Action",
        "Thriller",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_changes_directors(
    admin_client,
    db_session,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create_response.json()["uuid"]
        )
    )

    payload = movie_data()
    payload["directors"] = [
        "Steven Spielberg",
    ]

    response = await admin_client.patch(
        f"{MOVIES_URL}{movie.id}/",
        json=payload,
    )

    assert response.status_code == 200

    directors = {
        director["name"]
        for director in response.json()["directors"]
    }

    assert directors == {
        "Steven Spielberg",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_changes_stars(
    admin_client,
    db_session,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create_response.json()["uuid"]
        )
    )

    payload = movie_data()
    payload["stars"] = [
        "Tom Hanks",
    ]

    response = await admin_client.patch(
        f"{MOVIES_URL}{movie.id}/",
        json=payload,
    )

    assert response.status_code == 200

    stars = {
        star["name"]
        for star in response.json()["stars"]
    }

    assert stars == {
        "Tom Hanks",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_movie_success(
    admin_client,
    db_session,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create_response.json()["uuid"]
        )
    )

    response = await admin_client.delete(
        f"{MOVIES_URL}{movie.id}/",
    )

    assert response.status_code == 204

    deleted_movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.id == movie.id,
        )
    )

    assert deleted_movie is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_movie_not_found(
    admin_client,
):
    response = await admin_client.delete(
        f"{MOVIES_URL}999999/",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Movie not found."
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_requires_admin(
    client,
):
    response = await client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_requires_admin(
    admin_client,
    client,
    db_session,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create.json()["uuid"]
        )
    )

    response = await client.patch(
        f"{MOVIES_URL}{movie.id}/",
        json=movie_data(
            name="Updated",
        ),
    )

    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_movie_requires_admin(
    admin_client,
    client,
    db_session
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie = await db_session.scalar(
        select(MovieModel).where(
            MovieModel.uuid == create.json()["uuid"]
        )
    )

    response = await client.delete(
        f"{MOVIES_URL}{movie.id}/",
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_invalid_payload(
    admin_client,
):
    payload = movie_data()
    payload.pop("name")

    response = await admin_client.post(
        MOVIES_URL,
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_invalid_price(
    admin_client,
):
    payload = movie_data()
    payload["price"] = "-5"

    response = await admin_client.post(
        MOVIES_URL,
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_invalid_imdb(
    admin_client,
):
    payload = movie_data()
    payload["imdb"] = "15"

    response = await admin_client.post(
        MOVIES_URL,
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_movies_returns_empty_list(
    client,
):
    response = await client.get(
        MOVIES_URL,
        params={
            "search": "MovieThatDoesNotExist",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_unknown_genre(
    client,
):
    response = await client.get(
        MOVIES_URL,
        params={
            "genre": "UnknownGenre",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_unknown_director(
    client,
):
    response = await client.get(
        MOVIES_URL,
        params={
            "director": "Unknown Director",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_movies_unknown_star(
    client,
):
    response = await client.get(
        MOVIES_URL,
        params={
            "star": "Unknown Star",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_movie_validation_error(
    admin_client,
):
    response = await admin_client.post(
        MOVIES_URL,
        json={},
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_movie_validation_error(
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    response = await admin_client.patch(
        f"{MOVIES_URL}{movie_uuid}/",
        json={
            "year": -1,
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_movie_to_favorites_success(
    user_client,
    admin_client,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create_response.json()["uuid"]

    response = await user_client.post(
        f"/api/v1/profile/favorites/{movie_uuid}/",
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_movie_to_favorites_twice(
    user_client,
    admin_client,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create_response.json()["uuid"]

    response = await user_client.post(
        f"/api/v1/profile/favorites/{movie_uuid}/",
    )

    assert response.status_code == 204

    response = await user_client.post(
        f"/api/v1/profile/favorites/{movie_uuid}/",
    )

    assert response.status_code == 409


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_movie_to_favorites_movie_not_found(
    user_client,
):
    response = await user_client.post(
        "/api/v1/profile/favorites/00000000-0000-0000-0000-000000000000/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_movie_from_favorites_success(
    user_client,
    admin_client,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create_response.json()["uuid"]

    response = await user_client.post(
        f"/api/v1/profile/favorites/{movie_uuid}/",
    )

    assert response.status_code == 204

    response = await user_client.delete(
        f"/api/v1/profile/favorites/{movie_uuid}/",
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_movie_from_favorites_not_found(
    user_client,
):
    response = await user_client.delete(
        "/api/v1/profile/favorites/00000000-0000-0000-0000-000000000000/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_remove_movie_from_favorites_when_not_added(
    user_client,
    admin_client,
):
    create_response = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create_response.json()["uuid"]

    response = await user_client.delete(
        f"/api/v1/profile/favorites/{movie_uuid}/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_favorite_movies(
    user_client,
    admin_client,
):
    first = await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Movie 1",
        ),
    )

    second = await admin_client.post(
        MOVIES_URL,
        json=movie_data(
            name="Movie 2",
        ),
    )

    await user_client.post(
        f"/api/v1/profile/favorites/{first.json()['uuid']}/",
    )

    await user_client.post(
        f"/api/v1/profile/favorites/{second.json()['uuid']}/",
    )

    response = await user_client.get(
        "/api/v1/profile/favorites/",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2

    names = {
        movie["name"]
        for movie in body["items"]
    }

    assert names == {
        "Movie 1",
        "Movie 2",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_movie_success(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/rating/",
        json={
            "rating": 9,
        },
    )

    assert response.status_code == 204

    response = await user_client.get(
        f"{MOVIES_URL}{movie_uuid}/rating/",
    )

    assert response.status_code == 200
    assert response.json()["rating"] == 9


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_movie_updates_rating(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/rating/",
        json={
            "rating": 6,
        },
    )

    assert response.status_code == 204

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/rating/",
        json={
            "rating": 10,
        },
    )

    assert response.status_code == 204

    response = await user_client.get(
        f"{MOVIES_URL}{movie_uuid}/rating/",
    )

    assert response.status_code == 200
    assert response.json()["rating"] == 10


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_movie_not_found(
    user_client,
):
    response = await user_client.post(
        "/api/v1/movies/00000000-0000-0000-0000-000000000000/rating/",
        json={
            "rating": 8,
        },
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_movie_validation_error(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/rating/",
        json={
            "rating": 15,
        },
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_user_rating(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/rating/",
        json={
            "rating": 8,
        },
    )

    response = await user_client.get(
        f"{MOVIES_URL}{movie_uuid}/rating/",
    )

    assert response.status_code == 200
    assert response.json()["rating"] == 8


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_rating_success(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/rating/",
        json={
            "rating": 9,
        },
    )

    response = await user_client.delete(
        f"{MOVIES_URL}{movie_uuid}/rating/",
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_rating_not_found(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    response = await user_client.delete(
        f"{MOVIES_URL}{movie_uuid}/rating/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_comment_success(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Amazing movie!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["text"] == "Amazing movie!"
    assert body["parent_comment_uuid"] is None
    assert body["likes_count"] == 0
    assert body["replies_count"] == 0
    assert body["is_liked"] is False
    assert body["is_edited"] is False
    assert body["author"]["username"] == "admin"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_comment_movie_not_found(
    user_client,
):
    response = await user_client.post(
        "/api/v1/movies/00000000-0000-0000-0000-000000000000/comments/",
        json={
            "text": "Hello",
        },
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_reply_success(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    parent = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Parent",
        },
    )

    parent_uuid = parent.json()["uuid"]

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Reply",
            "parent_comment_uuid": parent_uuid,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["text"] == "Reply"
    assert body["parent_comment_uuid"] == parent_uuid


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_movie_comments(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "First",
        },
    )

    await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Second",
        },
    )

    response = await user_client.get(
        f"{MOVIES_URL}{movie_uuid}/comments/",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total_pages"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_comment_success(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    comment = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Old text",
        },
    )

    comment_uuid = comment.json()["uuid"]

    response = await user_client.patch(
        f"/api/v1/movies/comments/{comment_uuid}/",
        json={
            "text": "New text",
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "New text"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_comment_not_found(
    user_client,
):
    response = await user_client.patch(
        "/api/v1/movies/comments/00000000-0000-0000-0000-000000000000/",
        json={
            "text": "New",
        },
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_comment_success(
    user_client,
    admin_client,
):
    create = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = create.json()["uuid"]

    comment = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Delete me",
        },
    )

    comment_uuid = comment.json()["uuid"]

    response = await user_client.delete(
        f"/api/v1/movies/comments/{comment_uuid}/",
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_comment_not_found(
    user_client,
):
    response = await user_client.delete(
        "/api/v1/movies/comments/00000000-0000-0000-0000-000000000000/",
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_like_comment_success(
    user_client,
    admin_client,
):
    movie = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = movie.json()["uuid"]

    comment = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Nice movie",
        },
    )

    assert comment.status_code == 201

    comment_uuid = comment.json()["uuid"]

    response = await user_client.post(
        f"/api/v1/movies/comments/{comment_uuid}/like/"
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_like_comment_not_found(
    user_client,
):
    response = await user_client.post(
        "/api/v1/movies/comments/00000000-0000-0000-0000-000000000000/like/"
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_toggle_comment_like_success(
    user_client,
    admin_client,
):
    movie = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = movie.json()["uuid"]

    comment = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Nice movie",
        },
    )

    comment_uuid = comment.json()["uuid"]

    response = await user_client.post(
        f"/api/v1/movies/comments/{comment_uuid}/like/"
    )

    assert response.status_code == 204

    response = await user_client.post(
        f"/api/v1/movies/comments/{comment_uuid}/like/"
    )

    assert response.status_code == 204


@pytest.mark.integration
@pytest.mark.asyncio
async def test_comment_replies_tree(
    user_client,
    admin_client,
):
    movie = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = movie.json()["uuid"]

    parent = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Parent",
        },
    )

    parent_uuid = parent.json()["uuid"]

    await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Reply 1",
            "parent_comment_uuid": parent_uuid,
        },
    )

    await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={
            "text": "Reply 2",
            "parent_comment_uuid": parent_uuid,
        },
    )

    response = await user_client.get(
        f"{MOVIES_URL}{movie_uuid}/comments/",
    )

    assert response.status_code == 200

    root_comment = response.json()["items"][0]

    assert len(root_comment["replies"]) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_comments_empty(
    user_client,
    admin_client,
):
    movie = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = movie.json()["uuid"]

    response = await user_client.get(
        f"{MOVIES_URL}{movie_uuid}/comments/",
    )

    assert response.status_code == 200

    assert response.json()["items"] == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_comment_validation_error(
    user_client,
    admin_client,
):
    movie = await admin_client.post(
        MOVIES_URL,
        json=movie_data(),
    )

    movie_uuid = movie.json()["uuid"]

    response = await user_client.post(
        f"{MOVIES_URL}{movie_uuid}/comments/",
        json={},
    )

    assert response.status_code == 422
