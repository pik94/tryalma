When working with components in this directory:

- Use v1.healthcheck modules as an example of adding a new endpoint
- Use function-based style to add a create a new endpoint
- Define logic in router.py module
- Define schemas in schemas.py module
- If you need a database connection, use get_database_session dependency
- If you need to work with service, you MUST use get_container dependency and access the needed service through MainContainer
- If you need user_id, use auth_jwt dependency
- When adding a new router, include it to the main router using include_router