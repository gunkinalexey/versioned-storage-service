import base64
import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient


class FakeStorageClient:
    objects: dict[str, bytes] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def upload_file_by_link(
        self,
        link: str,
        data,
        file_size: int,
    ) -> None:
        if isinstance(data, bytes):
            uploaded_data = data
        else:
            chunks = []
            async for chunk in data:
                chunks.append(chunk)
            uploaded_data = b"".join(chunks)

        if len(uploaded_data) != file_size:
            raise ValueError("Invalid file size")
        self.objects[link] = uploaded_data

    async def delete_file_by_link(self, link: str) -> None:
        self.objects.pop(link, None)

    async def download_file_by_link(
        self,
        link: str,
        chunk_size: int = 1024 * 512,
    ):
        data = self.objects[link]
        for offset in range(0, len(data), 5):
            yield data[offset : offset + 5]

    @staticmethod
    async def test() -> bool:
        return True


class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_directory = tempfile.TemporaryDirectory()
        database_path = os.path.join(cls.temp_directory.name, "test.db")
        os.environ["SERVICE_DB_URL"] = f"sqlite+aiosqlite:///{database_path}"

        cls.storage_patcher = patch(
            "storage.storage.StorageClient",
            FakeStorageClient,
        )
        cls.storage_patcher.start()

        from main import app

        cls.test_client = TestClient(app, raise_server_exceptions=False)
        cls.client = cls.test_client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.test_client.__exit__(None, None, None)
        cls.storage_patcher.stop()
        cls.temp_directory.cleanup()

    def setUp(self):
        FakeStorageClient.objects.clear()

    def _create_version(self, collection_uuid, name="Example collection"):
        response = self.client.post(
            "/api/v1/version",
            json={
                "collection_uuid": str(collection_uuid),
                "name": name,
                "description": "Integration test version",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]["version_uuid"]

    def _set_single_item(
        self,
        collection_uuid,
        version_uuid,
        item_uuid,
        item_data,
    ):
        item_hash = hashlib.sha256(item_data).hexdigest()
        response = self.client.post(
            "/api/v1/items",
            json={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "items": [
                    {
                        "uuid": str(item_uuid),
                        "path": "config/example.json",
                        "data_hash": item_hash,
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["items_data_to_upload"],
            [str(item_uuid)],
        )
        return item_hash

    def _upload_stream(
        self,
        collection_uuid,
        version_uuid,
        item_uuid,
        item_data,
        item_hash,
    ):
        response = self.client.post(
            "/api/v1/data",
            headers={
                "Content-Length": str(len(item_data)),
                "X-File-Hash": item_hash,
                "X-Collection-UUID": str(collection_uuid),
                "X-Version-UUID": version_uuid,
                "X-Item-UUID": str(item_uuid),
                "Content-Type": "application/octet-stream",
            },
            content=iter([item_data[:9], item_data[9:18], item_data[18:]]),
        )
        self.assertEqual(response.status_code, 200)

    def _complete_version(self, collection_uuid, version_uuid):
        response = self.client.post(
            "/api/v1/version_complete",
            json={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
            },
        )
        self.assertEqual(response.status_code, 200)

    def _create_uploaded_version(self, collection_uuid, item_data):
        version_uuid = self._create_version(collection_uuid)
        item_uuid = uuid4()
        item_hash = self._set_single_item(
            collection_uuid,
            version_uuid,
            item_uuid,
            item_data,
        )
        self._upload_stream(
            collection_uuid,
            version_uuid,
            item_uuid,
            item_data,
            item_hash,
        )
        return version_uuid, item_uuid, item_hash

    def test_streaming_version_lifecycle(self):
        collection_uuid = uuid4()
        item_data = b"complete service example"
        version_uuid, item_uuid, _ = self._create_uploaded_version(
            collection_uuid,
            item_data,
        )
        self._complete_version(collection_uuid, version_uuid)

        collections_response = self.client.get("/api/v1/collection_list")
        self.assertEqual(collections_response.status_code, 200)
        current_versions = {
            collection["collection_uuid"]: collection["version_uuid"]
            for collection in collections_response.json()["data"]["collections"]
        }
        self.assertEqual(current_versions[str(collection_uuid)], version_uuid)

        manifest_response = self.client.get(
            "/api/v1/items",
            params={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
            },
        )
        self.assertEqual(manifest_response.status_code, 200)
        self.assertEqual(
            manifest_response.json()["data"]["items"][0]["path"],
            "config/example.json",
        )

        download_response = self.client.get(
            "/api/v1/data",
            params={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "item_uuid": str(item_uuid),
            },
        )
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response.content, item_data)
        self.assertEqual(
            download_response.headers["content-type"],
            "application/octet-stream",
        )

    def test_base64_upload_and_download(self):
        collection_uuid = uuid4()
        item_uuid = uuid4()
        item_data = b"small base64 payload"
        version_uuid = self._create_version(collection_uuid)
        item_hash = self._set_single_item(
            collection_uuid,
            version_uuid,
            item_uuid,
            item_data,
        )

        upload_response = self.client.post(
            "/api/v1/data_b64",
            json={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "item_uuid": str(item_uuid),
                "data_hash": item_hash,
                "data": base64.b64encode(item_data).decode("utf-8"),
            },
        )
        self.assertEqual(upload_response.status_code, 200)

        download_response = self.client.get(
            "/api/v1/data_b64",
            params={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "item_uuid": str(item_uuid),
            },
        )
        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(
            base64.b64decode(download_response.json()["data"]),
            item_data,
        )

    def test_cannot_complete_version_with_missing_data(self):
        collection_uuid = uuid4()
        version_uuid = self._create_version(collection_uuid)
        self._set_single_item(
            collection_uuid,
            version_uuid,
            uuid4(),
            b"not uploaded",
        )

        response = self.client.post(
            "/api/v1/version_complete",
            json={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_rejects_manifest_hash_mismatch(self):
        collection_uuid = uuid4()
        item_uuid = uuid4()
        item_data = b"base64 payload"
        version_uuid = self._create_version(collection_uuid)
        self._set_single_item(
            collection_uuid,
            version_uuid,
            item_uuid,
            item_data,
        )

        response = self.client.post(
            "/api/v1/data_b64",
            json={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "item_uuid": str(item_uuid),
                "data_hash": "0" * 64,
                "data": base64.b64encode(item_data).decode("utf-8"),
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(FakeStorageClient.objects, {})

    def test_rejects_stream_content_hash_mismatch_and_deletes_object(self):
        collection_uuid = uuid4()
        item_uuid = uuid4()
        expected_data = b"expected stream payload"
        actual_data = b"different stream data"
        version_uuid = self._create_version(collection_uuid)
        item_hash = self._set_single_item(
            collection_uuid,
            version_uuid,
            item_uuid,
            expected_data,
        )

        response = self.client.post(
            "/api/v1/data",
            headers={
                "Content-Length": str(len(actual_data)),
                "X-File-Hash": item_hash,
                "X-Collection-UUID": str(collection_uuid),
                "X-Version-UUID": version_uuid,
                "X-Item-UUID": str(item_uuid),
                "Content-Type": "application/octet-stream",
            },
            content=iter([b"different ", b"stream ", b"data"]),
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(FakeStorageClient.objects, {})

    def test_completed_version_is_immutable(self):
        collection_uuid = uuid4()
        item_data = b"immutable payload"
        version_uuid, item_uuid, item_hash = self._create_uploaded_version(
            collection_uuid,
            item_data,
        )
        self._complete_version(collection_uuid, version_uuid)

        response = self.client.post(
            "/api/v1/data_b64",
            json={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "item_uuid": str(item_uuid),
                "data_hash": item_hash,
                "data": base64.b64encode(item_data).decode("utf-8"),
            },
        )

        self.assertEqual(response.status_code, 409)

    def test_new_completed_version_replaces_current_version(self):
        collection_uuid = uuid4()
        first_version_uuid, _, _ = self._create_uploaded_version(
            collection_uuid,
            b"first version",
        )
        self._complete_version(collection_uuid, first_version_uuid)

        second_version_uuid, _, _ = self._create_uploaded_version(
            collection_uuid,
            b"second version",
        )
        self._complete_version(collection_uuid, second_version_uuid)

        response = self.client.get("/api/v1/collection_list")
        self.assertEqual(response.status_code, 200)
        matching_versions = [
            collection["version_uuid"]
            for collection in response.json()["data"]["collections"]
            if collection["collection_uuid"] == str(collection_uuid)
        ]
        self.assertEqual(matching_versions, [second_version_uuid])

    def test_returns_not_found_for_missing_collection(self):
        response = self.client.get(
            "/api/v1/items",
            params={
                "collection_uuid": str(uuid4()),
                "version_uuid": str(uuid4()),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_returns_not_found_for_missing_version(self):
        collection_uuid = uuid4()
        self._create_version(collection_uuid)

        response = self.client.get(
            "/api/v1/items",
            params={
                "collection_uuid": str(collection_uuid),
                "version_uuid": str(uuid4()),
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_returns_not_found_for_missing_item(self):
        collection_uuid = uuid4()
        version_uuid = self._create_version(collection_uuid)
        self._set_single_item(
            collection_uuid,
            version_uuid,
            uuid4(),
            b"known item",
        )

        response = self.client.get(
            "/api/v1/data",
            params={
                "collection_uuid": str(collection_uuid),
                "version_uuid": version_uuid,
                "item_uuid": str(uuid4()),
            },
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
