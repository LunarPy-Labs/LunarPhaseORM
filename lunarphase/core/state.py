import copy
from typing import Dict, Any, Set, List

try:
    from lunarphase._lunarphase_rs import StateTracker as RustStateTracker
    HAS_RUST_CORE = True
except ImportError:
    HAS_RUST_CORE = False

class PyStateTracker:
    """Pure Python fallback for StateTracker when Rust binary is unavailable."""
    def __init__(self):
        self._snapshot: Dict[str, Any] = {}
        self._current: Dict[str, Any] = {}

    def set_initial_state(self, data: Dict[str, Any]):
        self._snapshot = copy.deepcopy(data)
        self._current = copy.deepcopy(data)

    def set_field(self, field: str, value: Any):
        self._current[field] = value

    def get_field(self, field: str) -> Any:
        return self._current.get(field)

    def is_dirty(self) -> bool:
        for k, v in self._current.items():
            if k not in self._snapshot or self._snapshot[k] != v:
                return True
        return False

    def dirty_fields(self) -> List[str]:
        dirty = []
        for k, v in self._current.items():
            if k not in self._snapshot or self._snapshot[k] != v:
                dirty.append(k)
        return dirty

    def get_dirty_changes(self) -> Dict[str, Any]:
        return {k: self._current[k] for k in self.dirty_fields()}

    def hydrate_snapshot(self):
        self._snapshot = copy.deepcopy(self._current)

    def get_current_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self._current)


def create_state_tracker():
    """Factory function returning RustStateTracker if available, otherwise PyStateTracker."""
    if HAS_RUST_CORE:
        return RustStateTracker()
    return PyStateTracker()
