import libcst as cst
from collections import namedtuple
from os import path
from typing import Callable, Dict, Iterable, List, Any, Optional, Union, Tuple
from dynapyt.utils.nodeLocator import get_node_by_location
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from dynamicslicing.utils import AttributeMetaData, LineMetaData, VariableMetaData, CommentFinder, ElementMetaData, remove_lines

Location = namedtuple(
    "Location", ["file", "start_line",
                 "start_column", "end_line", "end_column"]
)

predefined_types = ["str", "bytes", "bytearray", "int", "float",
                      "complex", "list", "tuple", "dict", "set", "frozenset", "range"]


class SliceDataflow(BaseAnalysis):
    lines_info: Dict[int, LineMetaData] = dict()
    variables_info: Dict[str, VariableMetaData] = dict()
    sliced_function_name = "slice_me"
    slicing_comment = "slicing criterion"
    static_lines: List[int] = list()
    slice_start_line: int
    slice_end_line: int
    source: str = ""
    source_path: str = ""
    iids: Dict[Location, int] = None
    collections_modifiers_attributes = [
        "append", "extend", "insert", "remove", "pop", "clear", "reverse", "sort"]

    def __init__(self, source_path: str = ""):
        super(SliceDataflow, self).__init__()
        self.source = ""
        self.source_path = source_path
        self.lines_info = dict()
        self.variables_info = dict()
        self.slice_start_line = -1
        self.slice_end_line = -1

    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        if (location.start_line != location.end_line):
            return
        read_variables = self.extract_variables(dyn_ast, iid)
        _, attribute_name = self.read_is_via_attribute(dyn_ast, iid)
        if (read_variables is not None):
            dependencies: List[int] = []
            for variable in read_variables:
                for key, value in self.variables_info.items():
                    if key == variable:
                        dependencies.append(value.active_definition)
                        if attribute_name is None:
                            if (len(value.elements) > 0):
                                for _, line in value.elements.items():
                                    dependencies.append(line.active_definition)
                            if (len(value.attributes) > 0):
                                for _, line in value.attributes.items():
                                    dependencies.append(line.active_definition)
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
        lhs_variable, rhs_variable = self.reference_variable(dyn_ast, iid)
        if lhs_variable is not None and rhs_variable is not None and type(new_val).__name__ not in predefined_types:
            self.variables_info[rhs_variable].references.append(lhs_variable)
        variable_name, property_name, index = self.extract_lhs(dyn_ast, iid)
        if (variable_name is not None):
            if (property_name is not None):
                if (variable_name not in self.variables_info):
                    raise "ERROR"
                for ref in self.variables_info[variable_name].references:
                    if ref in self.variables_info:
                        self.variables_info[ref].attributes.update(
                            {property_name: AttributeMetaData(location.start_line)})
                self.variables_info[variable_name].attributes.update(
                    {property_name: AttributeMetaData(location.start_line)})
                dependencies: List[int] = []
                dependencies.append(
                    self.variables_info[variable_name].active_definition)
                if location.start_line in self.lines_info:
                    self.lines_info.get(
                        location.start_line).dependencies += dependencies
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        dependencies)
            elif (index is not None):
                if (variable_name not in self.variables_info):
                    raise "ERROR"
                self.variables_info[variable_name].elements.update(
                    {index: ElementMetaData(location.start_line)})
                dependencies: List[int] = []
                dependencies.append(
                    self.variables_info[variable_name].active_definition)
                self.variables_info[variable_name].previous_definition = self.variables_info[variable_name].active_definition
                self.variables_info[variable_name].active_definition = location.start_line
                if (index in self.variables_info):
                    dependencies.append(
                        self.variables_info[index].active_definition)
                if location.start_line in self.lines_info:
                    self.lines_info.get(
                        location.start_line).dependencies += dependencies
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        dependencies)
            else:
                if (variable_name in self.variables_info):
                    self.variables_info[variable_name].previous_definition = \
                        self.variables_info[variable_name].active_definition
                    self.variables_info[variable_name].active_definition = \
                        location.start_line
                    self.variables_info[variable_name].elements.clear()
                    self.variables_info[variable_name].attributes.clear()
                    self.variables_info[variable_name].references.clear()
                else:
                    self.variables_info[variable_name] = VariableMetaData(
                        location.start_line, type(new_val).__name__)

    def augmented_assignment(self, dyn_ast: str, iid: int, left: Any, op: str, right: Any) -> Any:
        variable_name, property_name, index = self.extract_lhs(dyn_ast, iid)
        location = self.iid_to_location(dyn_ast, iid)
        if (variable_name is not None):
            if (property_name is not None):
                if (variable_name not in self.variables_info):
                    raise "ERROR"
                self.variables_info[variable_name].attributes.update(
                    {property_name: AttributeMetaData(location.start_line)})
                dependencies: List[int] = []
                dependencies.append(
                    self.variables_info[variable_name].active_definition)
                if (f"{variable_name}.{property_name}" in self.variables_info):
                    dependencies.append(
                        self.variables_info[f"{variable_name}.{property_name}"].active_definition)
                if location.start_line in self.lines_info:
                    self.lines_info.get(
                        location.start_line).dependencies += dependencies
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        dependencies)
            elif (index is not None):
                if (variable_name not in self.variables_info):
                    raise "ERROR"
                self.variables_info[variable_name].elements.update(
                    {index: ElementMetaData(location.start_line)})
                dependencies: List[int] = []
                dependencies.append(
                    self.variables_info[variable_name].active_definition)
                if (index in self.variables_info):
                    dependencies.append(
                        self.variables_info[index].active_definition)
                if location.start_line in self.lines_info:
                    self.lines_info.get(
                        location.start_line).dependencies += dependencies
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        dependencies)
            else:
                dependencies: List[int] = []
                if (variable_name in self.variables_info):
                    dependencies.append(self.variables_info[variable_name].previous_definition)
                    self.variables_info[variable_name].previous_definition = \
                        self.variables_info[variable_name].active_definition
                    self.variables_info[variable_name].active_definition = \
                        location.start_line
                else:
                    self.variables_info[variable_name] = VariableMetaData(
                        location.start_line, None)
                    dependencies.append(location.start_line)

                if location.start_line in self.lines_info:
                    self.lines_info.get(
                        location.start_line).dependencies += dependencies
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        dependencies)    

    def read_attribute(self, dyn_ast: str, iid: int, base: Any, name: str, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if isinstance(node, cst.Attribute) and isinstance(node.value, cst.Name) and isinstance(node.attr, cst.Name):
            variable_name = node.value.value
            attribute_name = node.attr.value
            if (attribute_name in self.collections_modifiers_attributes):
                if (variable_name in self.variables_info):
                    self.variables_info[variable_name].previous_definition = \
                        self.variables_info[variable_name].active_definition
                    self.variables_info[variable_name].active_definition = location.start_line
            dependencies: List[int] = []
            for variable in [variable_name]:
                for key, value in self.variables_info.items():
                    if key == variable:
                        dependencies.append(value.active_definition)
                        if (attribute_name in value.attributes):
                            dependencies.append(
                                value.attributes[attribute_name].active_definition)
            if location.start_line in self.lines_info:
                self.lines_info.get(
                    location.start_line).dependencies += dependencies
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    dependencies)

    def read_subscript(self, dyn_ast: str, iid: int, base: Any, sl: List[Union[int, Tuple]], val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if isinstance(node, cst.Subscript) and isinstance(node.value, cst.Name):
            variable_name = node.value.value
            if (variable_name not in self.variables_info):
                raise "ERROR"
            dependencies: List[int] = []
            if (self.variables_info[variable_name].elements.get(str(sl[0])) is not None):
                dependencies.append(
                    self.variables_info[variable_name].elements[str(sl[0])].active_definition)
            else:
                dependencies.append(
                    self.variables_info[variable_name].active_definition)

            if location.start_line in self.lines_info:
                self.lines_info.get(
                    location.start_line).dependencies += dependencies
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    dependencies)

    def function_enter(self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool) -> None:
        location = self.iid_to_location(dyn_ast, iid)
        if (name == self.sliced_function_name):
            self.slice_start_line = location.start_line + 1
            self.slice_end_line = location.end_line

    def end_execution(self) -> None:
        for key, value in self.variables_info.items():
            print(
                f"Variables: {key} -- {value.active_definition} -- {value.elements} -- {value.typeOf}")
        for key, value in self.lines_info.items():
            print(f"Lines: {key} -- {value.dependencies}")

        self.prepare_file_attributes()

        slice_line_number = self.get_slicing_criterion_line(
            self.source, self.slicing_comment)

        lines_to_keep = self.compute_slice(slice_line_number)

        print(f"Number To Keep = {lines_to_keep}")
        print(
            f"Slice Min, Max = {self.slice_start_line}-{self.slice_end_line}")

        sliced_code = remove_lines(
            self.source, lines_to_keep, self.slice_start_line, self.slice_end_line)

        self.create_sliced_file(sliced_code)

    def reference_variable(self, dyn_ast: str, iid: int) -> (str, str):
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if isinstance(node, cst.Assign):
            if isinstance(node.targets[0], cst.AssignTarget):
                if isinstance(node.targets[0].target, cst.Name) and \
                        isinstance(node.value, cst.Name):
                    return node.targets[0].target.value, node.value.value
        return None, None

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

    def extract_lhs(self, dyn_ast: str, iid: int) -> (str, str, str):
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if (not isinstance(node, cst.Assign)) and (not isinstance(node, cst.AugAssign)):
            return None, None, None
        elif isinstance(node, cst.AugAssign):
            if isinstance(node.target, cst.Name):
                return node.target.value, None, None
            elif isinstance(node.target, cst.Subscript):
                return node.target.value.value, None, self.extract_subscript(node.target.slice[0])
            elif isinstance(node.target, cst.Attribute):
                if isinstance(node.target.value, cst.Name) and (node.target.attr, cst.Name):
                    return node.target.value.value, node.target.attr.value, None
        elif not isinstance(node.targets[0], cst.AssignTarget):
            return None, None, None
        elif isinstance(node.targets[0].target, cst.Name):
            return node.targets[0].target.value, None, None
        elif isinstance(node.targets[0].target, cst.Attribute):
            if (isinstance(node.targets[0].target.value, cst.Name) and
                    node.targets[0].target.value.value == 'self'):
                return None, None, None
            elif (isinstance(node.targets[0].target.value, cst.Name) and
                  isinstance(node.targets[0].target.attr, cst.Name)):
                return node.targets[0].target.value.value, node.targets[0].target.attr.value, None
            else:
                return node.targets[0].target.value, node.targets[0].target.attr, None
        elif isinstance(node.targets[0].target, cst.Subscript):
            return node.targets[0].target.value.value, None, self.extract_subscript(node.targets[0].target.slice[0])
        return None, None, None

    def extract_subscript(self, node: cst.SubscriptElement) -> str:
        if not isinstance(node.slice, cst.Index):
            return None

        if isinstance(node.slice.value, cst.Integer):
            return str(node.slice.value.value)
        elif isinstance(node.slice.value, cst.Name):
            return node.slice.value.value
        elif isinstance(node.slice.value, cst.UnaryOperation) and \
            isinstance(node.slice.value.operator, cst.Minus) and \
                isinstance(node.slice.value.expression, cst.Integer) \
            and node.slice.value.expression.value == '1':
            return '-1'

    def read_is_via_attribute(self, dyn_ast: str, iid: int) -> (str, str):
        self.prepare_file_attributes()
        if iid + 1 not in self.iids:
            return None, None
        current_location = self.iid_to_location(dyn_ast, iid)
        next_location = self.iid_to_location(dyn_ast, iid + 1)
        if current_location.start_line != next_location.start_line:
            return None, None
        elif current_location.start_column != next_location.start_column:
            return None, None
        elif current_location.end_column > next_location.end_column:
            return None, None
        lines = self.source.split('\n')
        expression = lines[current_location.start_line -
                           1][next_location.start_column:next_location.end_column]
        node = cst.parse_statement(expression)
        if isinstance(node, cst.SimpleStatementLine):
            if isinstance(node.body[0], cst.Expr):
                if isinstance(node.body[0].value, cst.Attribute):
                    if isinstance(node.body[0].value.value, cst.Name) and isinstance(node.body[0].value.attr, cst.Name):
                        return node.body[0].value.value.value, node.body[0].value.attr.value
        return None, None

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
        directory, file_name_extension = path.split(self.source_path)
        _, extension = path.splitext(file_name_extension)
        if extension == ".orig":
            slice_path = path.join(directory, "sliced.py")
        with open(slice_path, 'w') as file:
            file.write(sliced_code)

    def get_slicing_criterion_line(self, code: str, comment: str) -> int:
        syntax_tree = cst.parse_module(code)
        wrapper = cst.metadata.MetadataWrapper(syntax_tree)
        comment_finder = CommentFinder(comment)
        _ = wrapper.visit(comment_finder)
        return comment_finder.line_number

    def prepare_file_attributes(self):
        if self.source_path == "":
            self.source_path = next(iter(self.asts))

        if self.source == "":
            with open(self.source_path, "r") as file:
                self.source = file.read()

        if self.iids is None:
            self.iids = IIDs(self.source_path).iid_to_location
