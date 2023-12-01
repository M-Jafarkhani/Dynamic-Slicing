import libcst as cst
from typing import Callable, List, Any, Union, Tuple
from libcst._nodes.module import Module
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from dynapyt.utils.nodeLocator import get_node_by_location
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)

class CodeAnalyzerWrapper(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        PositionProvider,
    )

class SliceDataflow(BaseAnalysis):
    def __init__(self, source_path):
        super(SliceDataflow, self).__init__()
        if (source_path.endswith("program.py")) :
            self.iid_object = IIDs(source_path)
            self.source_path = source_path
            with open(source_path, "r") as file:
                self.source = file.read()
            syntax_tree = self.create_syntax_tree()
            new_code = self.slice_code(syntax_tree)
            self.create_sliced_file(new_code)

    def create_syntax_tree(self) -> Module:
        return cst.parse_module(self.source)
    
    def slice_code(self, syntax_tree: Module) -> str:
        wrapper = cst.metadata.MetadataWrapper(syntax_tree)
        code_modifier = CodeAnalyzerWrapper()
        new_syntax_tree = wrapper.visit(code_modifier)
        return new_syntax_tree.code

    def create_sliced_file(self, sliced_code: str) -> None:
        file_path = self.source_path.replace("/program.py", "/sliced.py")
        with open(file_path, 'w') as file:
            file.write(sliced_code)