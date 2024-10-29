import json
from typing import Any
from abc import ABC, abstractmethod


class BaseNode(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    def update_state(self, key: str, value: Any, is_pydantic=False):
        if is_pydantic:
            value = json.dumps(value.model_dump())
        if key in self.state and isinstance(self.state[key], list):
            self.state[key].append(value)
        else:
            self.state[key] = value
