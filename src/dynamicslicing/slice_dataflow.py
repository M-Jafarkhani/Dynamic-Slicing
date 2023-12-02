import libcst as cst
import os
from typing import Callable, Dict, List, Any, Union, Tuple
from dynapyt.utils.nodeLocator import get_node_by_location
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynamicslicing.utils import LineMetaData, VariableMetaData, CommentFinder, remove_lines

class SliceDataflow(BaseAnalysis):
    lines_info: Dict[int, LineMetaData] = dict()
    variables_info: Dict[str, VariableMetaData] = dict()
    sliced_function_name = "slice_me"
    slicing_comment = "slicing criterion"
    static_lines: List[int] = list()
    source: str = ""
    source_path: str = ""

    def __init__(self, source_path: str = ""):
        super(SliceDataflow, self).__init__()
        self.source_path = source_path

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

        self.source_path = next(iter(self.asts))
        with open(self.source_path, "r") as file:
            self.source = file.read()

        slice_line_number = self.get_slicing_criterion_line(
            self.source, self.slicing_comment)
        numbers_to_keep = self.compute_slice(slice_line_number)

        print(f"Number To Keep = {numbers_to_keep}")
        print(f"Static Lines = {self.static_lines}")

        sliced_code = remove_lines(
            self.source, numbers_to_keep + self.static_lines)
        
        self.create_sliced_file(sliced_code)

        print(f"============")
        print(f"")
        print(sliced_code)
        print(f"")
        print(f"============")

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
        slice_path: str = ""
        directory, file_name_extension = os.path.split(self.source_path)
        _, extension = os.path.splitext(file_name_extension)
        if extension == ".orig":
            slice_path = os.path.join(directory, "sliced.py")
        with open(slice_path, 'w') as file:
            file.write(sliced_code)

    def get_slicing_criterion_line(self, code: str, comment: str) -> int:
        syntax_tree = cst.parse_module(code)
        wrapper = cst.metadata.MetadataWrapper(syntax_tree)
        comment_finder = CommentFinder(comment)
        _ = wrapper.visit(comment_finder)
        return comment_finder.line_number