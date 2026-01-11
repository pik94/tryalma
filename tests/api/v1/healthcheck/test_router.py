import datetime as dt

from fastapi import status
from httpx import AsyncClient

from service.database.models.healthchecks import ServiceType


async def test_get_healthchecks(auth_jwt_test_client: AsyncClient, create_healthcheck):
    now = dt.datetime.now(dt.UTC)
    api_healthcheck = await create_healthcheck(type=ServiceType.API, timestamp=now - dt.timedelta(minutes=10))
    scheduler_healthcheck = await create_healthcheck(
        type=ServiceType.SCHEDULER, timestamp=now - dt.timedelta(minutes=15)
    )

    # Test getting all healthchecks
    rv = await auth_jwt_test_client.get('/api/v1/healthcheck')

    assert rv.status_code == status.HTTP_200_OK
    data = rv.json()
    assert 'items' in data
    assert len(data['items']) == 2

    # Verify we got the latest record for each type
    timestamps = {item['type']: item['timestamp'] for item in data['items']}
    assert timestamps[ServiceType.API] == api_healthcheck.timestamp.isoformat().replace('+00:00', 'Z')
    assert timestamps[ServiceType.SCHEDULER] == scheduler_healthcheck.timestamp.isoformat().replace('+00:00', 'Z')
