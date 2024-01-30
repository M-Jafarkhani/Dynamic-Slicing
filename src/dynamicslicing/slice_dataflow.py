import libcst as cst
from collections import namedtuple
from os import path
from typing import Callable, Dict, List, Any, Union, Tuple
from dynapyt.utils.nodeLocator import get_node_by_location
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from dynamicslicing.utils import AttributeMetaData, LineMetaData, VariableMetaData, CommentFinder, ElementMetaData, remove_lines

class SliceDataflow(BaseAnalysis):
    """
    This class runs slicing algorithm on a Python files, with a specified comment pointing to slicing criterion, 
    and creates another Python file named sliced.py with sliced code. This class only covers data flow analysis.

    Attributes
    ----------
    Location : namedtuple
        Duplicate defenition of Dyna-pyt Location named-tuple

    immutable_types : list
        A list of types that are immutable

    collections_modifiers_attributes: list
        A list of attributes that are changes a collection 

    lines_info: Dict[int, LineMetaData]
        A dictionary which hold the LineMetaData of every line number in code

    variables_info: Dict[str, VariableMetaData]
        A dictionary which hold the VariableMetaData of every variable in code

    sliced_function_name : str
        A fixed function name that slicing occuurs inside that

    slicing_comment : str
        A fixed comment which indicates the line which the slice should be computed

    static_lines: List[int]
        A list of line numbers which are out of slicing criterion

    slice_start_line: int
        The starting line number of slicing

    slice_end_line: int
        The end line number of slicing

    source: str
        The Python code before slicing

    source_path: str
        The path to the code file to be sliced

    iids: Dict[Location, int]
        A Dictionary that maps every iid to its Location

    start_analysis : bool
        Boolean variable which indicates the slicing computation should start or not
    -------
    """
    Location = namedtuple(
        "Location", ["file", "start_line",
                     "start_column", "end_line", "end_column"])
    immutable_types = ["int", "float", "complex", "bool", "str",
                       "bytes", "tuple", "frozenset"]
    collections_modifiers_attributes = [
        "append", "extend", "insert", "remove", "pop", "clear", "reverse", "sort"]
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
    start_analysis = False

    def __init__(self, source_path: str = ""):
        """
        Parameters
        ----------
        source_path: str
            The path to the code file to be sliced
        """
        super(SliceDataflow, self).__init__()
        self.source = ""
        self.source_path = source_path
        self.lines_info = dict()
        self.variables_info = dict()
        self.slice_start_line = -1
        self.slice_end_line = -1
        self.start_analysis = False

    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        """Hook for reading an object attribute. Here we update our meta-data which helps us to compute the slice.
        This hook is called when a read of a variable oocurs.

        E.g. `obj.attr`

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        base : Any
            The object to which the attribute is attached.

        name : str
            The name of the attribute.

        val : Any
            The resulting value.

        Returns
        -------
        Any
            If provided, overwrites the returned value.

        """
        if self.can_run_analysis(dyn_ast, iid) == False:
            return
        location = self.iid_to_location(dyn_ast, iid)
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
                    location.start_line).dependencies += list(set(dependencies))
                self.lines_info.get(location.start_line).dependencies = list(
                    set(self.lines_info.get(location.start_line).dependencies))
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    list(set(dependencies)))

    def write(self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any) -> Any:
        """Hook for writes. Here we update our meta-data which helps us to compute the slice.
        This hook is called when a write to a variable oocurs.

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        old_vals : Any
            A list of old values before the write takes effect.
            It's a list to support multiple assignments.
            Each old value is wrapped into a lambda function, so that
            the analysis writer can decide if and when to evaluate it.

        new_val : Any
            The value after the write takes effect.

        Returns
        -------
        Any
            If provided, overwrites the returned value.
        """
        if self.can_run_analysis(dyn_ast, iid) == False:
            return
        location = self.iid_to_location(dyn_ast, iid)

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
                        location.start_line).dependencies += list(set(dependencies))
                    self.lines_info.get(location.start_line).dependencies = list(
                        set(self.lines_info.get(location.start_line).dependencies))
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        list(set(dependencies)))
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

                lhs_variable, rhs_variable = self.reference_variable(
                    dyn_ast, iid)

                if lhs_variable is not None and rhs_variable is not None and type(new_val).__name__ not in self.immutable_types:
                    self.variables_info[rhs_variable].references.append(
                        lhs_variable)
                    if lhs_variable not in self.variables_info:
                        self.variables_info[lhs_variable] = VariableMetaData(
                            location.start_line, type(new_val).__name__)
                    self.variables_info[lhs_variable].references.append(
                        rhs_variable)

    def augmented_assignment(self, dyn_ast: str, iid: int, left: Any, op: str, right: Any) -> Any:
        """Hook for any augmented assignment. Here we update our meta-data which helps us to compute the slice.
        This hook is called when an augmented assinemnt is called.

        E.g. `a += 1`

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        left : Any
            The left operand.

        op : str
            The operator.

        right : Any
            The right operand.

        val : Any
            The resulting value.

        Returns
        -------
        Any
            If provided, overwrites the result.
        """
        if self.can_run_analysis(dyn_ast, iid) == False:
            return
        location = self.iid_to_location(dyn_ast, iid)
        variable_name, property_name, index = self.extract_lhs(dyn_ast, iid)
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
                        location.start_line).dependencies += list(set(dependencies))
                    self.lines_info.get(location.start_line).dependencies = list(
                        set(self.lines_info.get(location.start_line).dependencies))
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        list(set(dependencies)))
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
                        location.start_line).dependencies += list(set(dependencies))
                    self.lines_info.get(location.start_line).dependencies = list(
                        set(self.lines_info.get(location.start_line).dependencies))
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        list(set(dependencies)))
            else:
                dependencies: List[int] = []
                if (variable_name in self.variables_info):
                    dependencies.append(
                        self.variables_info[variable_name].previous_definition)
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
                        location.start_line).dependencies += list(set(dependencies))
                    self.lines_info.get(location.start_line).dependencies = list(
                        set(self.lines_info.get(location.start_line).dependencies))
                else:
                    self.lines_info[location.start_line] = LineMetaData(
                        list(set(dependencies)))

    def read_attribute(self, dyn_ast: str, iid: int, base: Any, name: str, val: Any) -> Any:
        """Hook for reading an object attribute. Here we update our meta-data which helps us to compute the slice.
        This hook is called when a read of attribute from an object is called.

        E.g. `obj.attr`

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        base : Any
            The object to which the attribute is attached.

        name : str
            The name of the attribute.

        val : Any
            The resulting value.

        Returns
        -------
        Any
            If provided, overwrites the returned value.
        """
        if self.can_run_analysis(dyn_ast, iid) == False:
            return
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if isinstance(node, cst.Attribute) and isinstance(node.value, cst.Name) and isinstance(node.attr, cst.Name):
            variable_name = node.value.value
            attribute_name = node.attr.value
            if (attribute_name in self.collections_modifiers_attributes) or (type(val).__name__ == "method"):
                previous_definition = self.variables_info[variable_name].active_definition
                self.variables_info[variable_name].previous_definition = previous_definition
                self.variables_info[variable_name].active_definition = location.start_line
                for reference in self.variables_info[variable_name].references:
                    previous_definition = self.variables_info[reference].active_definition
                    self.variables_info[reference].previous_definition = previous_definition
                    self.variables_info[reference].active_definition = location.start_line
            dependencies: List[int] = []

            dependencies.append(
                self.variables_info[variable_name].active_definition)
            if (attribute_name in self.variables_info[variable_name].attributes):
                dependencies.append(
                    self.variables_info[variable_name].attributes[attribute_name].active_definition)
            for reference in self.variables_info[variable_name].references:
                dependencies.append(
                    self.variables_info[reference].previous_definition)

            if location.start_line in self.lines_info:
                self.lines_info.get(
                    location.start_line).dependencies += list(set(dependencies))
                self.lines_info.get(location.start_line).dependencies = list(
                    set(self.lines_info.get(location.start_line).dependencies))
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    list(set(dependencies)))

    def read_subscript(self, dyn_ast: str, iid: int, base: Any, sl: List[Union[int, Tuple]], val: Any) -> Any:
        """Hook for reading a subscript, also known as a slice. Here we update our meta-data which helps us to compute the slice.
        This hook is called when a read of subscript from an object (array) is called.

        E.g. `obj[1, 2]`

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        base : Any
            The object to which the subscript is attached.

        sl : List[Union[int, Tuple]]
            The subscript.

        val : Any
            The resulting value.

        Returns
        -------
        Any
            If provided, overwrites the returned value.
        """
        if self.can_run_analysis(dyn_ast, iid) == False:
            return
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
                    location.start_line).dependencies += list(set(dependencies))
                self.lines_info.get(location.start_line).dependencies = list(
                    set(self.lines_info.get(location.start_line).dependencies))
            else:
                self.lines_info[location.start_line] = LineMetaData(
                    list(set(dependencies)))

    def function_enter(self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool) -> None:
        """Hook for when an instrumented function is entered. Here we update our meta-data which helps us to compute the slice.
        This hook is called before enring a function. We check that if thee function name is matched with sliced_function_name, 
        then we set slice_start_line, slice_end_line and trigger the start_analysis 

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        args : List[Any]
            The arguments passed to the function.

        name:
            Name of the function called.

        is_lambda : bool
            Whether the function is a lambda function.
        """
        location = self.iid_to_location(dyn_ast, iid)
        if (name == self.sliced_function_name):
            self.slice_start_line = location.start_line + 1
            self.slice_end_line = location.end_line
            self.start_analysis = True

    def end_execution(self) -> None:
        """Hook for the end of execution. Here we reached end of exuction, so we have to compute slice and create slice.py file
        """
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
        """We check whether an assignment is an object's attribute

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        Returns
        -------
        (str, str)
            Returns two strings, object name and object attribute if it is an access to the object's attribute, otherwise returns None, None
        """
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if isinstance(node, cst.Assign):
            if isinstance(node.targets[0], cst.AssignTarget):
                if isinstance(node.targets[0].target, cst.Name) and \
                        isinstance(node.value, cst.Name):
                    return node.targets[0].target.value, node.value.value
        return None, None

    def extract_variables(self, dyn_ast: str, iid: int) -> List[str]:
        """We extract a list of variables which were used on the left-hand side

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        Returns
        -------
        List[str]
            A list of vvariables used on the left-hand side
        """
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
        """We extract a tuple of 3 strings, which corresponds to variable name, index and attribute name, respectively

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        Returns
        -------
        (str, str, str)
            A tuple of 3 strings: variable name, index and attribute name, respectively. Values could be None if not the case
        """
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
        """We extract subscript of an Index-access

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        Returns
        -------
        str
            The accessed index, if applicable, otherwise None
        """
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
        """Here we check whether a read is an access to object's attribute

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        Returns
        -------
        (str, str)
            A tuple consisting of object's name and its attribute, otherwise None
        """
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
        """A recursive method for computing the slice based on the meta-data that was computed during the execution. 
        We should call this method with the line number that contains the slicing criterion.

        Parameters
        ----------
        slice_line_number : int
            The line number that points to the current slicing line

        Returns
        -------
        List[int]
            A list of line numbers that should be kept
        """
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
        """This method creates the slice.py file

        Parameters
        ----------
        sliced_code: str
            Sliced Python code that should be written inside sliced.py file

        Returns
        -------
        None
        """
        slice_path: str = ""
        directory, file_name_extension = path.split(self.source_path)
        _, extension = path.splitext(file_name_extension)
        if extension == ".orig":
            slice_path = path.join(directory, "sliced.py")
        with open(slice_path, 'w') as file:
            file.write(sliced_code)

    def get_slicing_criterion_line(self, code: str, comment: str) -> int:
        """This method finds the line number that contains a specific comment

        Parameters
        ----------
        code: str
            The raw Python code before slicing, which contains a line that with the specified comment

        comment: str    
            The specified comment that we are looking for its line number
        Returns
        -------
        int
            Returns the line number that contains the specified comment
        """
        syntax_tree = cst.parse_module(code)
        wrapper = cst.metadata.MetadataWrapper(syntax_tree)
        comment_finder = CommentFinder(comment)
        _ = wrapper.visit(comment_finder)
        return comment_finder.line_number

    def prepare_file_attributes(self):
        """This method prepares source_path, source and iids after the execution 

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.source_path == "":
            self.source_path = next(iter(self.asts))

        if self.source == "":
            with open(self.source_path, "r") as file:
                self.source = file.read()

        if self.iids is None:
            self.iids = IIDs(self.source_path).iid_to_location

    def can_run_analysis(self, dyn_ast: str, iid: int) -> bool:
        """This method checks whether we can run analysis inside current node.

        Parameters
        ----------
        dyn_ast : str
            The path to the original code. Can be used to extract the syntax tree.

        iid : int
            Unique ID of the syntax tree node.

        Returns
        -------
        bool
            A boolean which indicates whether we are in a line (node) that could be analized for sliciing
        """
        if self.start_analysis == False:
            return False
        location = self.iid_to_location(dyn_ast, iid)
        if (location.start_line < self.slice_start_line):
            return False
        if (location.start_line > self.slice_end_line):
            return False
        return True
