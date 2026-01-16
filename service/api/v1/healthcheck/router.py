from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession


from service.api.v1.healthcheck.schemas import HealthChecksResponse
from service.container import MainContainer
from service.deps import get_database_session, get_container

router = APIRouter()


@router.get(
    '/healthcheck',
    response_model=HealthChecksResponse,
    status_code=status.HTTP_200_OK,
)
async def get_healthcheck(
    db_session: AsyncSession = Depends(get_database_session),
    container: MainContainer = Depends(get_container),
):
    """Get the latest healthcheck for each service type."""
    healthchecks = await container.healthcheck_service.get_last_healthchecks_per_type(db_session)
    return HealthChecksResponse(items=healthchecks)
