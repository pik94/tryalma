When working with components in this directory:

- When adding a new service, use the next structure:
  - service_name
    - __init__.py
    - service.py
- A new service class must be implemented in service.py and has a suffix Service, for example, like for UserService, HealthCheckService etc
- A new service object must be added to the MainContainer class from container.py with the following format:
    ```
    @cached_property
    def some_stuff_service(self) -> SomeStuffService:
        return SomeStuffService()
    ```
   You can check def healthcheck_service as the hint