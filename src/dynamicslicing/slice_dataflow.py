import libcst as cst
import os
from typing import Callable, Dict, List, Any, Union, Tuple
from dynapyt.utils.nodeLocator import get_node_by_location
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynamicslicing.utils import LineMetaData, VariableMetaData, CommentFinder, ElementMetaData, remove_lines


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
        variable_name, property_name, index = self.extract_lhs(dyn_ast, iid)
        print(f"{location.start_line} => {variable_name} - {property_name} - {index}")
        if (variable_name is not None):
            if (property_name is not None):
                pass
            elif (index is not None):
                if (variable_name not in self.variables_info):
                    raise "ERROR"
                self.variables_info[variable_name].elements.update({index: ElementMetaData(location.start_line)})
            else:
                if (variable_name in self.variables_info):
                    self.variables_info[variable_name].previous_definition = \
                        self.variables_info[variable_name].active_definition
                    self.variables_info[variable_name].active_definition = \
                        location.start_line
                else:
                    self.variables_info[variable_name] = VariableMetaData(location.start_line)    

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
            else:
                self.variables_info[variable_name
                                    ] = VariableMetaData(location.start_line)

    def read_subscript(self, dyn_ast: str, iid: int, base: Any, sl: List[Union[int, Tuple]], val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if isinstance(node, cst.Subscript) and isinstance(node.value, cst.Name):
            variable_name = node.value.value
            if (variable_name not in self.variables_info):
                raise "ERROR"
            dependencies: List[int] = []
            if (self.variables_info[variable_name].elements.get(str(sl[0])) is not None):
                dependencies.append(self.variables_info[variable_name].elements[str(sl[0])].active_definition)  
            else:
                dependencies.append(self.variables_info[variable_name].active_definition)  
            
            if location.start_line in self.lines_info:
                self.lines_info.get(location.start_line).dependencies += dependencies
            else:
                self.lines_info[location.start_line] = LineMetaData(dependencies)

    def function_enter(self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool) -> None:
        location = self.iid_to_location(dyn_ast, iid)
        if (name == self.sliced_function_name):
            self.slice_start_line = location.start_line + 1
            self.slice_end_line = location.end_line
        
    def end_execution(self) -> None:
        for key, value in self.variables_info.items():
            print(f"Variables: {key} -- {value.active_definition} -- {value.elements}")
        for key, value in self.lines_info.items():
            print(f"Lines: {key} -- {value.dependencies}")
        
        self.source_path = next(iter(self.asts))
        with open(self.source_path, "r") as file:
            self.source = file.read()
        
        #print(cst.parse_module(self.source))
        
        slice_line_number = self.get_slicing_criterion_line(
            self.source, self.slicing_comment)
        
        lines_to_keep = self.compute_slice(slice_line_number)

        print(f"Number To Keep = {lines_to_keep}")
        print(f"Slice Min, Max = {self.slice_start_line}-{self.slice_end_line}")

        sliced_code = remove_lines(
            self.source, lines_to_keep, self.slice_start_line, self.slice_end_line)

        #print(sliced_code)

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

    def extract_lhs(self, dyn_ast: str, iid: int) -> (str,str,int):
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if (not isinstance(node, cst.Assign)) and (not isinstance(node, cst.AugAssign)):
            return None, None, None
        elif isinstance(node, cst.AugAssign):
            if isinstance(node.target, cst.Name):
                return node.target.value, None, None
        elif not isinstance(node.targets[0], cst.AssignTarget):
            return None, None, None
        if isinstance(node.targets[0].target, cst.Name):
            return node.targets[0].target.value, None, None
        elif isinstance(node.targets[0].target, cst.Name):
            return node.targets[0].target.value, None, None        
        elif isinstance(node.targets[0].target, cst.Subscript):
            if isinstance(node.targets[0].target.value, cst.Name):
                variable_name = node.targets[0].target.value.value
                slice_index: int = None 
                if isinstance(node.targets[0].target.slice[0], cst.SubscriptElement) and \
                    isinstance(node.targets[0].target.slice[0].slice, cst.Index) and \
                        isinstance(node.targets[0].target.slice[0].slice.value, cst.Integer):
                            slice_index = node.targets[0].target.slice[0].slice.value.value
                return variable_name, None, slice_index
        return None, None, None
    
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
