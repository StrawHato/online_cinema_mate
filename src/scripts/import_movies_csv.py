import asyncio
import csv
import random
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.database.models.movies import MovieModel
from src.database.session import AsyncSessionLocal
from src.services.movies import MovieService


CERTIFICATIONS = [
    "G",
    "PG",
    "PG-13",
    "R",
]

DIRECTORS = [
    "Christopher Nolan",
    "Steven Spielberg",
    "Martin Scorsese",
    "Ridley Scott",
    "Quentin Tarantino",
    "James Cameron",
    "Peter Jackson",
    "David Fincher",
    "Guy Ritchie",
    "Denis Villeneuve",
]


BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "imdb_movies.csv"


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None

    value = value.strip()

    if not value or value.lower() == "nan":
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_imdb(value: str | None) -> Decimal:
    score = parse_decimal(value)

    if score is None:
        return Decimal("0")

    if score > 10:
        score /= Decimal("10")

    return score


async def import_movies() -> None:

    async with AsyncSessionLocal() as db:
        if not CSV_PATH.exists():
            raise FileNotFoundError(
                f"CSV file not found: {CSV_PATH}"
            )

        with open(
            CSV_PATH,
            encoding="utf-8",
            newline=""
        ) as csv_file:

            reader = csv.DictReader(csv_file)

            imported = 0

            for row in reader:

                name = row["names"].strip()

                try:
                    year = int(str(row["date_x"])[:4])
                except (ValueError, TypeError):
                    continue

                existing = await MovieService.get_movie_by_name_and_year(
                    db,
                    name,
                    year,
                )

                if existing:
                    continue

                certification = (
                    await MovieService.get_or_create_certification(
                        random.choice(CERTIFICATIONS),
                        db
                    )
                )

                genres = (
                    await MovieService.get_or_create_genres(
                        [
                            g.strip()
                            for g in row["genre"].split(",")
                            if g.strip()
                        ],
                        db,
                    )
                )

                stars = (
                    await MovieService.get_or_create_stars(
                        [
                            s.strip()
                            for s in row["crew"].split(",")[:4]
                            if s.strip()
                        ],
                        db
                    )
                )

                directors = (
                    await MovieService.get_or_create_directors(
                        [
                            random.choice(DIRECTORS)
                        ],
                        db,
                    )
                )

                movie = MovieModel(
                    name=name,
                    year=year,
                    time=random.randint(80, 180),
                    imdb=parse_imdb(row["score"]),
                    votes=random.randint(
                        2_000,
                        1_000_000,
                    ),
                    meta_score=random.randint(
                        45,
                        95,
                    ),
                    gross=parse_decimal(row["revenue"]),
                    description=row["overview"] or "",
                    price=Decimal(
                        f"{random.randint(5, 20)}.99"
                    ),
                    certification=certification,
                    genres=genres,
                    stars=stars,
                    directors=directors,
                )

                db.add(movie)

                imported += 1

                if imported % 100 == 0:
                    await db.commit()
                    print(f"Imported {imported} movies...")

            await db.commit()

            print(f"Done! Imported {imported} movies.")


if __name__ == "__main__":
    asyncio.run(import_movies())
