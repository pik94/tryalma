Please read the description of this directory:
- add: tests for api
- database: tests for database
- services: tests for services
- tasks: tests for tasks

If you asked to generate a new fixture for database object, use the same pattern like create_healthcheck and import this fixture in 
tests/conftest.py. Add "# noqa: F401" after the importing