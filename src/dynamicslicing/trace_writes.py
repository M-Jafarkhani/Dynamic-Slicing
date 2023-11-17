from typing import Callable, List, Any
from dynapyt.analyses.BaseAnalysis import BaseAnalysis

class TraceWritesAnalysis(BaseAnalysis):
    def __init__(self) -> None:
        super(TraceWritesAnalysis, self).__init__()

    def write(
        self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any
    ) -> Any:
        print(f'{new_val}')