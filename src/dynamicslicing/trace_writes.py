import libcst as cst
from typing import Callable, List, Any, Union, Tuple
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.utils.nodeLocator import get_node_by_location
from utils import get_slicing_criterion_line
class VariableMetaData():
    name: str
    firstDefinition: int

    def __init__(self, name: str, firstDefinition: int) -> None:
        self.name = name
        self.firstDefinition = firstDefinition
class LineMetaData():
    number: int
    dependencies: List[int] = []

    def __init__(self, number: int, dependencies: List[int]) -> None:
        self.number = number
        self.dependencies = dependencies

class TraceWritesAnalysis(BaseAnalysis):
    def __init__(self) -> None:
        super(TraceWritesAnalysis, self).__init__()
        self.linesInfo : List[LineMetaData] = list()
        self.variablesInfo : List[VariableMetaData] = list()

    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast,iid)
        if (location.start_line != location.end_line):
            return
        readVariables = self.extract_variables(dyn_ast,iid)
        
        if (readVariables is not None):
            dependencies: List[int] = []
            for variable in readVariables:
               
                for variable_metadata in self.variablesInfo:
                    if variable_metadata.name == variable:
                        dependencies.append(variable_metadata.firstDefinition)
            found = False
            for lineInfo in self.linesInfo:
                if lineInfo.number == location.start_line:
                    lineInfo.dependencies += dependencies
                    found = True
            if not found:
                self.linesInfo.append(LineMetaData(location.start_line, dependencies))

    def write(self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any) -> Any:
        location = self.iid_to_location(dyn_ast,iid)
        if (location.start_line != location.end_line):
            return
        writeVariable = self.extract_variables(dyn_ast,iid)
        if ((writeVariable is not None) and len(writeVariable) == 1):
            found = False
            for variable_metadata in self.variablesInfo:
                if variable_metadata.name == writeVariable[0]:
                    variable_metadata.firstDefinition = location.start_line
                    found = True
            if (not found):
                self.variablesInfo.append(VariableMetaData(writeVariable[0],location.start_line))

    def read_attribute(self, dyn_ast: str, iid: int, base: Any, name: str, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast,iid)

    def read_subscript(self, dyn_ast: str, iid: int, base: Any, sl: List[Union[int, Tuple]], val: Any) -> Any:
        location = self.iid_to_location(dyn_ast,iid)

    def end_execution(self) -> None:
        # for v in self.variablesInfo:
        #     print(f"{v.name} -- {v.firstDefinition}")
        # for i in self.linesInfo:
        #     print(f"{i.number} -- {i.dependencies}")
         
        filePath = next(iter(self.asts))
        print(get_slicing_criterion_line(filePath)) 

    def extract_variables(self, dyn_ast: str, iid: int) -> List[str]:
        location = self.iid_to_location(dyn_ast,iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        variables : List[str] = []

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
          
    