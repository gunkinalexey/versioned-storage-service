import datetime
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import database.db_models as db_models
import models.schemas.schemas as models
from database.database import AsyncSessionLocal
from database.rollback_on_error_wrapper import rollback_on_error
from exceptions.exceptions import (
    CollectionNotFoundError,
    DataAlreadyUploadedError,
    DataHashError,
    DataUploadIncompleteError,
    InvalidVersionStateError,
    ItemConflictError,
    ItemNotFoundError,
    VersionNotFoundError,
)
from models.schemas.responses import CollectionVersion


class AsyncClient:
    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    async def create(cls) -> "AsyncClient":
        return cls(AsyncSessionLocal())

    async def close(self) -> None:
        await self.session.close()

    async def _get_collection(
        self,
        collection_uuid: uuid.UUID,
    ) -> db_models.Collection:
        result = await self.session.execute(
            select(db_models.Collection).where(
                db_models.Collection.uuid == str(collection_uuid)
            )
        )
        collection = result.scalar_one_or_none()
        if collection is None:
            raise CollectionNotFoundError(collection_uuid)
        return collection

    async def _get_version(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
    ) -> db_models.Version:
        collection = await self._get_collection(collection_uuid)
        result = await self.session.execute(
            select(db_models.Version).where(
                db_models.Version.collection_id == collection.id,
                db_models.Version.uuid == str(version_uuid),
            )
        )
        version = result.scalar_one_or_none()
        if version is None:
            raise VersionNotFoundError(collection_uuid, version_uuid)
        return version

    async def _get_item(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        item_uuid: uuid.UUID,
    ) -> tuple[db_models.Version, db_models.Item]:
        version = await self._get_version(collection_uuid, version_uuid)
        result = await self.session.execute(
            select(db_models.Item).where(
                db_models.Item.version_id == version.id,
                db_models.Item.uuid == str(item_uuid),
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise ItemNotFoundError(collection_uuid, version_uuid, item_uuid)
        return version, item

    @rollback_on_error
    async def create_version(self, version_model: models.Version) -> None:
        result = await self.session.execute(
            select(db_models.Collection).where(
                db_models.Collection.uuid == str(version_model.collection_uuid)
            )
        )
        collection = result.scalar_one_or_none()
        if collection is None:
            collection = db_models.Collection(uuid=str(version_model.collection_uuid))
            self.session.add(collection)
            await self.session.flush()

        result = await self.session.execute(
            select(db_models.Version).where(
                db_models.Version.collection_id == collection.id,
                db_models.Version.version_state.in_(
                    ["uploading_items", "uploading_data"]
                ),
            )
        )
        for incomplete_version in result.scalars().all():
            incomplete_version.version_state = "aborted"

        version = db_models.Version(
            collection_id=collection.id,
            uuid=str(version_model.uuid),
            creation_time=datetime.datetime.fromtimestamp(
                version_model.creation_time,
                tz=datetime.timezone.utc,
            ),
            modification_time=datetime.datetime.fromtimestamp(
                version_model.modification_time,
                tz=datetime.timezone.utc,
            ),
            version_state=version_model.version_state,
            name=version_model.name,
            description=version_model.description,
        )
        self.session.add(version)
        await self.session.commit()

    @rollback_on_error
    async def insert_items(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        items: List[models.Item],
    ) -> List[uuid.UUID]:
        version = await self._get_version(collection_uuid, version_uuid)
        self._check_version_state(
            collection_uuid,
            version,
            action="set items",
            required_state=["uploading_items"],
        )

        item_uuids = [item.uuid for item in items]
        item_paths = [item.path for item in items]
        if len(item_uuids) != len(set(item_uuids)) or len(item_paths) != len(
            set(item_paths)
        ):
            raise ItemConflictError()

        for item in items:
            self.session.add(
                db_models.Item(
                    version_id=version.id,
                    uuid=str(item.uuid),
                    path=item.path,
                    data_hash=item.data_hash,
                    storage_link=(
                        f"{collection_uuid}/{version_uuid}/{item.uuid}"
                    ),
                    uploaded=False,
                )
            )

        version.version_state = "uploading_data"
        version.modification_time = datetime.datetime.now(datetime.timezone.utc)
        await self.session.commit()
        return item_uuids

    async def validate_upload_and_get_link(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        item_uuid: uuid.UUID,
        data_hash: str,
    ) -> str:
        version, item = await self._get_item(
            collection_uuid,
            version_uuid,
            item_uuid,
        )
        self._check_version_state(
            collection_uuid,
            version,
            action="upload item data",
            required_state=["uploading_data"],
        )
        if item.uploaded:
            raise DataAlreadyUploadedError(item_uuid)
        if item.data_hash != data_hash:
            raise DataHashError(item.data_hash, data_hash)
        return str(item.storage_link)

    @rollback_on_error
    async def complete_file_upload(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        item_uuid: uuid.UUID,
    ) -> None:
        version, item = await self._get_item(
            collection_uuid,
            version_uuid,
            item_uuid,
        )
        self._check_version_state(
            collection_uuid,
            version,
            action="complete item upload",
            required_state=["uploading_data"],
        )
        item.uploaded = True
        version.modification_time = datetime.datetime.now(datetime.timezone.utc)
        await self.session.commit()

    @rollback_on_error
    async def complete_version(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
    ) -> None:
        version = await self._get_version(collection_uuid, version_uuid)
        self._check_version_state(
            collection_uuid,
            version,
            action="complete version",
            required_state=["uploading_data"],
        )

        result = await self.session.execute(
            select(db_models.Item).where(
                db_models.Item.version_id == version.id,
                db_models.Item.uploaded.is_(False),
            )
        )
        missing_items = [uuid.UUID(item.uuid) for item in result.scalars().all()]
        if missing_items:
            raise DataUploadIncompleteError(
                collection_uuid,
                version_uuid,
                missing_items,
            )

        result = await self.session.execute(
            select(db_models.Version).where(
                db_models.Version.collection_id == version.collection_id,
                db_models.Version.version_state == "current",
            )
        )
        current_version = result.scalar_one_or_none()
        if current_version is not None:
            current_version.version_state = "outdated"

        version.version_state = "current"
        version.modification_time = datetime.datetime.now(datetime.timezone.utc)
        await self.session.commit()

    async def get_collections(self, name_filter: str) -> List[CollectionVersion]:
        result = await self.session.execute(
            select(db_models.Collection, db_models.Version)
            .join(
                db_models.Version,
                db_models.Version.collection_id == db_models.Collection.id,
            )
            .where(db_models.Version.version_state == "current")
            .order_by(db_models.Version.modification_time.desc())
        )
        response = []
        for collection, version in result.all():
            if name_filter and name_filter.lower() not in version.name.lower():
                continue
            response.append(
                CollectionVersion(
                    collection_uuid=uuid.UUID(collection.uuid),
                    version_uuid=uuid.UUID(version.uuid),
                    name=version.name,
                    description=version.description,
                    creation_time=version.creation_time.timestamp(),
                    modification_time=version.modification_time.timestamp(),
                )
            )
        return response

    async def get_items(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
    ) -> List[models.Item]:
        version = await self._get_version(collection_uuid, version_uuid)
        result = await self.session.execute(
            select(db_models.Item)
            .where(db_models.Item.version_id == version.id)
            .order_by(db_models.Item.path)
        )
        return [
            models.Item(
                uuid=uuid.UUID(item.uuid),
                path=item.path,
                data_hash=item.data_hash,
            )
            for item in result.scalars().all()
        ]

    async def get_data_link(
        self,
        collection_uuid: uuid.UUID,
        version_uuid: uuid.UUID,
        item_uuid: uuid.UUID,
    ) -> str:
        _, item = await self._get_item(
            collection_uuid,
            version_uuid,
            item_uuid,
        )
        if not item.uploaded:
            raise ItemNotFoundError(collection_uuid, version_uuid, item_uuid)
        return str(item.storage_link)

    @staticmethod
    def _check_version_state(
        collection_uuid: uuid.UUID,
        version: db_models.Version,
        action: str,
        required_state: List[str],
    ) -> None:
        if version.version_state not in required_state:
            raise InvalidVersionStateError(
                collection_uuid=collection_uuid,
                version_uuid=uuid.UUID(version.uuid),
                current_version_state=version.version_state,
                action=action,
                required_state=required_state,
            )
