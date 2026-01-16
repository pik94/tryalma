import random
import string
import uuid


class BlobStorageService:
    @classmethod
    async def upload(cls, data: bytes) -> str:
        """Upload bytes data and return a URL string.

        Args:
            data: The bytes data to upload

        Returns:
            A string representing the URL of the uploaded data
        """
        # Generate a random URL string for demonstration
        random_id = str(uuid.uuid4())
        return f'https://blob-storage.example.com/{random_id}'

    @classmethod
    async def get(cls, key: str) -> bytes | None:
        """Get bytes data by the given string key.

        Args:
            key: The string key to retrieve data for

        Returns:
            Random bytes data or None if not found
        """
        # Return random bytes for demonstration
        if not key:
            return None

        # Generate random bytes (simulating stored data)
        random_size = random.randint(100, 1000)
        return bytes(''.join(random.choices(string.ascii_letters + string.digits, k=random_size)), 'utf-8')
