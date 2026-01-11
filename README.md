# Service
Service

## Dev stack run
1. Run dev stack
```bash
make dev-stack-run
```
2. Run migrations
```bash
alembic upgrade head
```
3.Install packages
```bash
uv sync 
```
4.Run scheduler
```bash
PYTHONPATH=. uv run python service/web_app.py 
```
5.Run web app
```bash
PYTHONPATH=. uv run python service/web_app.py 
```

You can also run all service in docker:
```bash
make PROFILE=dev-app dev-stack-up
```

## Tests
1. Run test stack
```bash
make test-stack-up
```