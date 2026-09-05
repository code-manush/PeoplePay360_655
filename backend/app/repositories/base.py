"""
Base repository interface.
Replace DummyXxxRepository with AivenXxxRepository to integrate PostgreSQL.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        pass

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> T:
        pass

    @abstractmethod
    def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        pass
