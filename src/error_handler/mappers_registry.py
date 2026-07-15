class ErrorMapperRegistry:
    def __init__(self) -> None:
        self._maps: dict[str, dict[type[Exception], int]] = {}

    def register_mapper(self, name: str, mapping: dict[type[Exception], int]) -> None:
        self._maps[name] = dict(mapping)

    def unregister_mapper(self, name: str) -> None:
        self._maps.pop(name, None)

    def resolve_status_code(
        self,
        exc: Exception,
        default_status_code: int = 500,
    ) -> int:
        merged: dict[type[Exception], int] = {}
        for mapping in self._maps.values():
            merged.update(mapping)

        for exc_type in type(exc).mro():
            if exc_type in merged:
                return merged[exc_type]

        return default_status_code


error_mapper_registry = ErrorMapperRegistry()
