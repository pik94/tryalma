from service.services.blob_storage.service import BlobStorageService


class TestBlobStorageService:
    async def test_upload_returns_string_url(self):
        """Test that upload method returns a string URL."""
        test_data = b'test data content'

        result = await BlobStorageService.upload(test_data)

        assert isinstance(result, str)
        assert result.startswith('https://blob-storage.example.com/')
        assert len(result) > len('https://blob-storage.example.com/')

    async def test_upload_with_empty_bytes(self):
        """Test upload method with empty bytes."""
        test_data = b''

        result = await BlobStorageService.upload(test_data)

        assert isinstance(result, str)
        assert result.startswith('https://blob-storage.example.com/')

    async def test_upload_with_large_data(self):
        """Test upload method with larger data."""
        test_data = b'x' * 10000  # 10KB of data

        result = await BlobStorageService.upload(test_data)

        assert isinstance(result, str)
        assert result.startswith('https://blob-storage.example.com/')

    async def test_get_returns_bytes_or_none(self):
        """Test that get method returns bytes or None."""
        test_key = 'test-key-123'

        result = await BlobStorageService.get(test_key)

        assert result is None or isinstance(result, bytes)

    async def test_get_with_valid_key_returns_bytes(self):
        """Test get method with a valid key returns bytes."""
        test_key = 'valid-key'

        result = await BlobStorageService.get(test_key)

        # Since we're returning random bytes, we should get bytes back
        assert isinstance(result, bytes)
        assert len(result) > 0

    async def test_get_with_empty_key_returns_none(self):
        """Test get method with empty key returns None."""
        result = await BlobStorageService.get('')

        assert result is None

    async def test_get_with_none_key_returns_none(self):
        """Test get method with None key returns None."""
        result = await BlobStorageService.get(None)

        assert result is None

    async def test_multiple_uploads_return_different_urls(self):
        """Test that multiple uploads return different URLs."""
        test_data = b'same data'

        url1 = await BlobStorageService.upload(test_data)
        url2 = await BlobStorageService.upload(test_data)

        assert url1 != url2
        assert isinstance(url1, str)
        assert isinstance(url2, str)

    async def test_get_returns_different_data_for_different_keys(self):
        """Test that get method returns different data for different keys."""
        key1 = 'key-1'
        key2 = 'key-2'

        data1 = await BlobStorageService.get(key1)
        data2 = await BlobStorageService.get(key2)

        # Both should return bytes
        assert isinstance(data1, bytes)
        assert isinstance(data2, bytes)
        # They should be different (very high probability with random data)
        assert data1 != data2
