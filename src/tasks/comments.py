import asyncio

import aiosmtplib
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.celery_app import celery_app
from src.config.dependencies import get_accounts_email_notificator
from src.database.models.accounts import (
    UserModel,
    UserProfileModel,
)
from src.database.models.movies import (
    MovieCommentLikeModel,
    MovieCommentModel,
    MovieModel,
)
from src.database.session import AsyncSessionLocal


@celery_app.task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_comment_reply_email_task(
    comment_id: int,
):
    asyncio.run(
        _send_comment_reply_email(
            comment_id,
        )
    )


async def _send_comment_reply_email(
    comment_id: int,
) -> None:

    async with AsyncSessionLocal() as db:

        stmt = (
            select(MovieCommentModel)
            .options(
                selectinload(MovieCommentModel.user)
                .selectinload(UserModel.profile),
                selectinload(MovieCommentModel.parent)
                .selectinload(MovieCommentModel.user)
                .selectinload(UserModel.profile),
                selectinload(MovieCommentModel.movie),
            )
            .where(
                MovieCommentModel.id == comment_id,
            )
        )

        result = await db.execute(stmt)

        comment = result.scalar_one_or_none()

        if (
            comment is None
            or comment.parent is None
        ):
            return

        if comment.parent.user_id == comment.user_id:
            return

        sender = get_accounts_email_notificator()

        await sender.send_comment_reply_email(
            email=comment.parent.user.email,
            username=(
                comment.parent.user.profile.username
                or comment.parent.user.email
            ),
            movie_name=comment.movie.name,
            comment_text=comment.parent.text,
            reply_text=comment.text,
        )


@celery_app.task(
    autoretry_for=(
        aiosmtplib.SMTPException,
        ConnectionError,
    ),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_comment_like_email_task(
    like_id: int,
):
    asyncio.run(
        _send_comment_like_email(
            like_id,
        )
    )


async def _send_comment_like_email(
    like_id: int,
) -> None:

    async with AsyncSessionLocal() as db:

        stmt = (
            select(MovieCommentLikeModel)
            .options(
                selectinload(MovieCommentLikeModel.user)
                .selectinload(UserModel.profile),
                selectinload(MovieCommentLikeModel.comment)
                .selectinload(MovieCommentModel.user)
                .selectinload(UserModel.profile),
                selectinload(MovieCommentLikeModel.comment)
                .selectinload(MovieCommentModel.movie),
            )
            .where(
                MovieCommentLikeModel.id == like_id,
            )
        )

        result = await db.execute(stmt)

        like = result.scalar_one_or_none()

        if like is None:
            return

        if like.user_id == like.comment.user_id:
            return

        sender = get_accounts_email_notificator()

        await sender.send_comment_like_email(
            email=like.comment.user.email,
            username=(
                like.comment.user.profile.username
                or like.comment.user.email
            ),
            movie_name=like.comment.movie.name,
            comment_text=like.comment.text,
            liked_by=(
                like.user.profile.username
                or like.user.email
            ),
        )
