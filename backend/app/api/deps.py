from fastapi import Depends, Request
from sqlalchemy.orm import Session

from backend.app.repositories.analyses import AnalysesRepository
from backend.app.repositories.reviews import ReviewsRepository
from backend.app.services.review import ReviewDeps


def get_db_session(request: Request):
    # The app creates one shared session factory at startup. Each request gets
    # a fresh Session from that factory, then closes it when the request ends.
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_analyses_repository(session: Session = Depends(get_db_session)) -> AnalysesRepository:
    return AnalysesRepository(session)


def get_reviews_repository(session: Session = Depends(get_db_session)) -> ReviewsRepository:
    return ReviewsRepository(session)


def get_review_deps(
    analyses_repository: AnalysesRepository = Depends(get_analyses_repository),
    reviews_repository: ReviewsRepository = Depends(get_reviews_repository),
) -> ReviewDeps:
    return ReviewDeps(
        analyses_repository=analyses_repository,
        reviews_repository=reviews_repository,
    )
