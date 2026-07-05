# 🎬 Online Cinema API

> A production-ready REST API for an online cinema platform built with **FastAPI**.
>
> The project demonstrates modern backend development practices, including authentication, payments, asynchronous background processing, cloud object storage, Docker, CI/CD pipelines and AWS deployment.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Docker](https://img.shields.io/badge/Docker-2496ED)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF)
![AWS](https://img.shields.io/badge/AWS-EC2-FF9900)
![License](https://img.shields.io/badge/License-MIT-green)

------------------------------------------------------------------------

# 📖 About

Online Cinema API is a backend service that provides everything required
for an online movie platform.

The project demonstrates production-oriented backend development using
**FastAPI**, asynchronous **SQLAlchemy**, **PostgreSQL**, **Docker**,
**Celery**, **Redis**, **MinIO**, **Stripe**, automated testing and
deployment to **AWS EC2**.

The goal of the project was not only to implement business logic, but
also to build a complete backend infrastructure ready for deployment.

------------------------------------------------------------------------

## ✨ Key Highlights

- 📦 Production deployment with Nginx + Docker + AWS EC2
- 🚀 Production-ready FastAPI backend
- 🔐 JWT Authentication + Google OAuth
- 💳 Stripe Payment Integration
- 🐳 Docker & Docker Compose
- ⚙️ GitHub Actions CI/CD
- 📧 Email Notifications
- 🗂️ MinIO Object Storage
- 🧪 154 Automated Tests

------------------------------------------------------------------------

# ✨ Features

## 👤 Authentication

-   JWT Access & Refresh tokens
-   User registration
-   Email account activation
-   Login / Logout
-   Password reset

## 👤 User Profile

-   Profile editing
-   Avatar upload
-   Avatar storage in MinIO
-   User favorites

## 🎥 Movies

-   CRUD operations
-   Genres
-   Actors
-   Languages
-   Search
-   Filtering
-   Pagination
-   Ratings
-   Comments

## 🛒 Shopping

-   Shopping cart
-   Orders
-   Stripe payments

## ⚙ Background Tasks

-   Celery
-   Redis
-   Email notifications

## ☁ Infrastructure

-   Docker
-   Docker Compose
-   Nginx
-   PostgreSQL
-   AWS EC2 deployment
-   GitHub Actions CI/CD

------------------------------------------------------------------------

# 🛠 Tech Stack

| Layer | Technologies |
|:------|:-------------|
| **Backend** | FastAPI, SQLAlchemy Async, Pydantic |
| **Database** | PostgreSQL, Alembic |
| **Authentication** | JWT |
| **Background Tasks** | Celery, Redis |
| **Storage** | MinIO (S3 Compatible) |
| **Payments** | Stripe |
| **Email** | SMTP, MailHog |
| **Testing** | Pytest |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions |
| **Deployment** | AWS EC2 |

------------------------------------------------------------------------

# 🚀 Live Demo

## 🌍 Deployed Project

**URL**

``` text
http://63.184.207.240/
```

------------------------------------------------------------------------

## 📚 Swagger

``` text
http://63.184.207.240/docs/
```

------------------------------------------------------------------------

## 🔐 Basic Authentication

Credentials are configured through environment variables:
- `NGINX_BASIC_AUTH_USER`
- `NGINX_BASIC_AUTH_PASSWORD`

------------------------------------------------------------------------

## 📄 Project Documentation (Google Docs)

``` text
https://docs.google.com/document/d/1WALBuKEwngC0CzORHeiTlB-a02esxu-C9ufewacl1Fo/edit?tab=t.0
```

------------------------------------------------------------------------

## ✅ GitHub Actions

- Flake8 linting
- Automated testing
- Production deployment to AWS EC2

### 📸 GitHub Actions Screenshot

<img width="1284" height="250" alt="image" src="https://github.com/user-attachments/assets/d5cb257b-c62b-4ea0-abfe-2122b33433ba" />


------------------------------------------------------------------------

# 📁 Project Structure

``` text
src/
├── config/
├── database/
├── notifications/
├── payments/
├── routes/
├── schemas/
├── security/
├── services/
├── storages/
├── tasks/
├── validation/
└── tests/
```

------------------------------------------------------------------------

# ⚙ Environment Variables

Create a `.env` file based on `.env.sample`.

Configure at least:

-   PostgreSQL
-   Redis
-   JWT Secrets
-   SMTP
-   MinIO
-   Stripe
-   Google OAuth
-   Nginx Basic Auth

------------------------------------------------------------------------

# 🚀 Local Development

## Poetry

``` bash
poetry install
poetry shell
uvicorn src.main:app --reload
```

## Docker

``` bash
docker compose -f docker-compose-dev.yml up --build
```

------------------------------------------------------------------------

# 🧪 Running Tests

``` bash
poetry run pytest src/tests
```

or

``` bash
docker compose -f docker-compose-dev.yml up -d
poetry run pytest src/tests
```

------------------------------------------------------------------------

# 🔄 CI/CD

The project uses GitHub Actions:

-   Lint (flake8)
-   Automated tests
-   Production deployment
-   AWS EC2

------------------------------------------------------------------------

# 📚 API Modules

-   Accounts
-   Profile
-   Movies
-   Genres
-   Actors
-   Languages
-   Shopping Cart
-   Orders
-   Payments
-   Ratings
-   Comments
-   Favorites

------------------------------------------------------------------------

# 📌 Future Improvements

-   Recommendation system
-   Watch history
-   Reviews moderation
-   Email verification improvements
-   Monitoring
-   HTTPS with Let's Encrypt

------------------------------------------------------------------------

# 📜 License

This project was created for educational and portfolio purposes.
