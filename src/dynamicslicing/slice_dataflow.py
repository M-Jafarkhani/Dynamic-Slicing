import libcst as cst
from typing import Callable, Dict, List, Any, Union, Tuple
from dynapyt.instrument.IIDs import IIDs
from dynapyt.utils.nodeLocator import get_node_by_location
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)
from libcst._nodes.statement import SimpleStatementLine, BaseStatement, For, If, Else, While

class VariableMetaData():
    active_definition: int
    previous_definition: int

    def __init__(self, active_definition: int) -> None:
        self.active_definition = active_definition
        self.previous_definition = -1

class LineMetaData():
    dependencies: List[int] = []
    slice_computed: bool

    def __init__(self, dependencies: List[int]) -> None:
        self.dependencies = dependencies
        self.slice_computed = False

class SliceDataflow(BaseAnalysis):
    lines_info: Dict[int, LineMetaData] = dict()
    variables_info: Dict[str, VariableMetaData] = dict()
    sliced_function_name = "slice_me"
    slicing_comment = "slicing criterion"
    static_lines: List[int] = list()
    source: str = ""
    source_path: str = ""

    def __init__(self, source_path):
        super(SliceDataflow, self).__init__()
        if (source_path.endswith("program.py")):
            self.iid_object = IIDs(source_path)
            self.source_path = source_path
            with open(source_path, "r") as file:
                self.source = file.read()

    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        if (location.start_line != location.end_line):
            return
        read_variables = self.extract_variables(dyn_ast, iid)
        if (read_variables is not None):
            dependencies: List[int] = []
            for variable in read_variables:
                for key, value in self.variables_info.items():
                    if key == variable:
                        dependencies.append(value.active_definition)

            if location.start_line in self.lines_info:
                self.lines_info.get(
                    location.start_line).dependencies += dependencies
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    dependencies)

    def write(self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        if (location.start_line != location.end_line):
            return
        write_variable = self.extract_variables(dyn_ast, iid)
        if ((write_variable is not None) and len(write_variable) == 1):
            if (write_variable[0] in self.variables_info):
                self.variables_info[write_variable[0]
                                    ].previous_definition = self.variables_info[write_variable[0]
                                                                                ].active_definition
                self.variables_info[write_variable[0]
                                    ].active_definition = location.start_line
            else:
                self.variables_info[write_variable[0]
                                    ] = VariableMetaData(location.start_line)

    def augmented_assignment(self, dyn_ast: str, iid: int, left: Any, op: str, right: Any) -> Any:
        left_variable = self.extract_variables(dyn_ast, iid)
        location = self.iid_to_location(dyn_ast, iid)
        if (left_variable is not None):
            dependencies: List[int] = []
            for key, value in self.variables_info.items():
                if key == left_variable[0]:
                    dependencies.append(value.previous_definition)

            if location.start_line in self.lines_info:
                self.lines_info.get(
                    location.start_line).dependencies += dependencies
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    dependencies)

    def read_attribute(self, dyn_ast: str, iid: int, base: Any, name: str, val: Any) -> Any:
        pass

    def read_subscript(self, dyn_ast: str, iid: int, base: Any, sl: List[Union[int, Tuple]], val: Any) -> Any:
        pass

    def pre_call(self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict):
        location = self.iid_to_location(dyn_ast, iid)
        if (function.__qualname__ == self.sliced_function_name):
            self.static_lines.append(location.start_line)

    def function_enter(self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool) -> None:
        location = self.iid_to_location(dyn_ast, iid)
        if (name == self.sliced_function_name):
            self.static_lines.append(location.start_line)

    def end_execution(self) -> None:
        for key, value in self.variables_info.items():
            print(f"{key} -- {value.active_definition}")
        for key, value in self.lines_info.items():
            print(f"{key} -- {value.dependencies}")

        file_path = next(iter(self.asts))
        slice_line_number = self.get_slicing_criterion_line(
            file_path, self.slicing_comment)
        numbers_to_keep = self.compute_slice(slice_line_number)

        print(f"Number To Keep = {numbers_to_keep}")
        print(f"Static Lines = {self.static_lines}")

        sliced_code = self.remove_lines(
            self.source, numbers_to_keep + self.static_lines)
        self.create_sliced_file(sliced_code)

    def extract_variables(self, dyn_ast: str, iid: int) -> List[str]:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        variables: List[str] = []
        if isinstance(node, cst.Name):
            variables.append(node.value)
        elif isinstance(node, cst.Assign):
            for target in node.targets:
                if isinstance(target, cst.AssignTarget) & isinstance(target.target, cst.Name):
                    variables.append(target.target.value)
        elif isinstance(node, cst.AugAssign):
            if isinstance(node.target, cst.Name):
                variables.append(node.target.value)
        return variables

    def compute_slice(self, slice_line_number: int) -> List[int]:
        result: List[int] = list()
        result.append(slice_line_number)
        if (slice_line_number in self.lines_info):
            if (self.lines_info[slice_line_number].slice_computed == False):
                self.lines_info[slice_line_number].slice_computed = True
                result = result + \
                    self.lines_info[slice_line_number].dependencies
                for item in self.lines_info[slice_line_number].dependencies:
                    result = result + self.compute_slice(item)
        return list(set(result))

    def create_sliced_file(self, sliced_code: str) -> None:
        file_path = self.source_path.replace("/program.py", "/sliced.py")
        print(f'### {self.source_path} $$$')  
        with open(file_path, 'w') as file:
            file.write(sliced_code)
          

    def remove_lines(self, code: str, lines_to_keep: List[int]) -> str:
        syntax_tree = cst.parse_module(code)
        wrapper = cst.metadata.MetadataWrapper(syntax_tree)
        code_modifier = RemoveLines(lines_to_keep)
        new_syntax_tree = wrapper.visit(code_modifier)
        return new_syntax_tree.code

    def get_slicing_criterion_line(self, source_path: str, comment: str) -> int:
        with open(source_path, "r") as file:
            code = file.read()
        syntax_tree = cst.parse_module(code)
        wrapper = cst.metadata.MetadataWrapper(syntax_tree)
        comment_finder = CommentFinder(comment)
        _ = wrapper.visit(comment_finder)
        return comment_finder.line_number   

class RemoveLines(cst.CSTTransformer):
    """
    Remove lines that are not included in a given array.
    """
    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        PositionProvider,
    )

    def __init__(self, lines_to_keep: List[int]) -> None:
        self.lines_to_keep = lines_to_keep

    def leave_For(self, original_node: For, updated_node: For) -> cst.For:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line not in self.lines_to_keep:
            return cst.RemoveFromParent()
        return updated_node

    def leave_While(self, original_node: While, updated_node: While) -> cst.While:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line not in self.lines_to_keep:
            return cst.RemoveFromParent()
        return updated_node

    def leave_If(self, original_node: If, updated_node: If) -> cst.If:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line not in self.lines_to_keep:
            return cst.RemoveFromParent()
        return updated_node

    def leave_Else(self, original_node: Else, updated_node: Else) -> cst.Else:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line not in self.lines_to_keep:
            return cst.RemoveFromParent()
        return updated_node

    def leave_SimpleStatementLine(self, original_node: SimpleStatementLine, updated_node: SimpleStatementLine) -> BaseStatement:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line not in self.lines_to_keep:
            return cst.RemoveFromParent()
        return updated_node

class CommentFinder(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider
    )
     
    def __init__(self, target_comment):
        self.target_comment = target_comment
        self.line_number = -1

    def visit_Comment(self, node: cst.Comment) -> None:
        if self.target_comment in node.value:
            location = self.get_metadata(PositionProvider, node)
            self.line_number = location.start.line
