When working with components in this directory:

- If you need to add a new group of env vars, create a class with prefix "Settings" and inherit it from BaseSettings
- Add a "model_config = SettingsConfigDict(env_prefix='<some_prefix>')" to the class definition. As a hint follow database_settings.py as example
- When adding new env vars, add them to ./configs/.env.dev and ./configs/.env.test. Use upper case for names and use prefix from the previous point
