from abc import ABC, abstractmethod
from typing import Optional


class CodeProvider(ABC):
    @abstractmethod
    def get_code(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_remaining_seconds(self) -> Optional[int]:
        pass
