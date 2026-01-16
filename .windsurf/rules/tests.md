---
trigger: manual
description: 
globs: 
---

- You MUST NOT rewrite existing unit tests if you have not asked about that
- You MUST use existing features if possible, and create a new one only if you cannot use any existing ones
- You can patch existing tests only if you are directly asked about that
- When writing tests, you must use the narrowest fixture. I.e. for example, if you need to create a specific database object, you must use appropriate fixture. For example, for creating healtcheck object, you MUST use create_healtchec fixture. If there is no such a fixture, you MUST create it.
- You MUST not use decorator @pytest.mark.asyncio fo async tests