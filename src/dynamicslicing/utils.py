from typing import Dict, List
import libcst as cst
from libcst._nodes.statement import SimpleStatementLine, BaseStatement, For, If, Else, While
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)
import libcst.matchers as m

class ControlFlowMetaData():
    """
    This class stores meta-data about a control flow 

    Attributes
    ----------
    start_line : int
        Start line number of control-flow

    iid : int
        Unique number that dyna-pyt assigns to the control-flow
    -------
    """
    start_line: int
    iid: int

    def __init__(self, start_line: int, iid: int) -> None:
        self.start_line = start_line
        self.iid = iid


class ElementMetaData():
    """
    This class stores meta-data about an element-access of a variable

    Attributes
    ----------
    active_definition : int
        Line number that points to the current (active) defenition of the variable's element

    previous_definition : int
        Line number that points to the previous active defenition of the variable's element
    -------
    """
    active_definition: int
    previous_definition: int

    def __init__(self, active_definition: int) -> None:
        self.active_definition = active_definition
        self.previous_definition = -1


class AttributeMetaData():
    """
    This class stores meta-data about an attribute-access of a variable

    Attributes
    ----------
    active_definition : int
        Line number that points to the current (active) defenition of the variable's attribute

    previous_definition : int
        Line number that points to the previous active defenition of the variable's attribute
    -------
    """
    active_definition: int
    previous_definition: int

    def __init__(self, active_definition: int) -> None:
        self.active_definition = active_definition
        self.previous_definition = -1


class VariableMetaData():
    """
    This class stores meta-data about a variable

    Attributes
    ----------
    active_definition : int
        Line number that points to the current (active) defenition of the variable

    previous_definition : int
        Line number that points to the previous active defenition of of the variable

    elements: Dict[str, ElementMetaData]
        A dictionary that contains meta-data about the variable's elements

    attributes: Dict[str, AttributeMetaData]
        A dictionary that contains meta-data about the variable's attributes   

    typeOf: str
        Stores the variable's type 

    references: List[str]
        A list of variables names that are references to this variable       
    -------
    """
        
    active_definition: int
    previous_definition: int
    elements: Dict[str, ElementMetaData] = dict()
    attributes: Dict[str, AttributeMetaData] = dict()
    typeOf: str
    references: List[str] = list()

    def __init__(self, active_definition: int, typeOf: str) -> None:
        self.active_definition = active_definition
        self.previous_definition = -1
        self.elements = dict()
        self.attributes = dict()
        self.typeOf = typeOf
        self.references = list()


class LineMetaData():
    """
    This class stores meta-data about one line of code

    Attributes
    ----------
    dependencies: List[int]
        A list of line numbers that are dependent to this line

    slice_computed: bool
        A boolean that indicates whether the slicing have been computed for this line       
    -------
    """
    dependencies: List[int] = []
    slice_computed: bool

    def __init__(self, dependencies: List[int]) -> None:
        self.dependencies = dependencies
        self.slice_computed = False


class OddIfNegation(m.MatcherDecoratableTransformer):
    """
    Negate the test of every if statement on an odd line.
    """
    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        PositionProvider,
    )

    def leave_If(self, original_node: If, updated_node: If) -> cst.If:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line % 2 == 0:
            return updated_node
        negated_test = cst.UnaryOperation(
            operator=cst.Not(),
            expression=updated_node.test,
        )
        return updated_node.with_changes(
            test=negated_test,
        )


class RemoveLines(cst.CSTTransformer):
    """
    Remove lines that are not included in a given array.
    """
    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        PositionProvider,
    )

    def __init__(self, lines_to_keep: List[int], slice_start_line: int, slice_end_line: int) -> None:
        """
        Parameters
        ----------
        lines_to_keep: List[int]
            A list of intergers than specifies which line numbers should be kept

        slice_start_line: int
            The start line number for slicing 

        slice_end_line: int
            The end line number for slicing 
        """
        self.lines_to_keep = lines_to_keep
        self.slice_start_line = slice_start_line
        self.slice_end_line = slice_end_line

    def leave_Comment(self, original_node: cst.Comment, updated_node: cst.Comment) -> cst.Comment:
        """
        Parameters
        ----------
        original_node: cst.Comment
            Original comment node in AST 
        updated_node: cst.Comment
            Update node in AST

        Returns
        ----------
        cst.Comment
            Returns removing command if the original comment node is in slicing range and not in lines_to_keep list,
            otherwise returns the updated_node     
        """
        location = self.get_metadata(PositionProvider, original_node)
        if (location.start.line not in self.lines_to_keep) and (self.slice_start_line <= location.start.line <= self.slice_end_line):
            return cst.RemoveFromParent()
        return updated_node

    def leave_For(self, original_node: For, updated_node: For) -> cst.For:
        """
        Parameters
        ----------
        original_node: cst.For
            Original for node in AST 

        updated_node: cst.For
            Update node in AST

        Returns
        ----------
        cst.For
            Returns removing command if the original for node is in slicing range and not in lines_to_keep list,
            otherwise returns the updated_node     
        """
        location = self.get_metadata(PositionProvider, original_node)
        if (location.start.line not in self.lines_to_keep) and (self.slice_start_line <= location.start.line <= self.slice_end_line):
            return cst.RemoveFromParent()
        return updated_node

    def leave_While(self, original_node: While, updated_node: While) -> cst.While:
        """
        Parameters
        ----------
        original_node: cst.While
            Original for node in AST 

        updated_node: cst.While
            Update node in AST

        Returns
        ----------
        cst.While
            Returns removing command if the original while node is in slicing range and not in lines_to_keep list,
            otherwise returns the updated_node     
        """
        location = self.get_metadata(PositionProvider, original_node)
        if (location.start.line not in self.lines_to_keep) and (self.slice_start_line <= location.start.line <= self.slice_end_line):
            return cst.RemoveFromParent()
        return updated_node

    def leave_If(self, original_node: If, updated_node: If) -> cst.If:
        """
        Parameters
        ----------
        original_node: cst.If
            Original if node in AST 

        updated_node: cst.If
            Update node in AST

        Returns
        ----------
        cst.If
            Returns removing command if the original if node is in slicing range and not in lines_to_keep list,
            otherwise returns the updated_node     
        """      
        location = self.get_metadata(PositionProvider, original_node)
        if (location.start.line not in self.lines_to_keep) and (self.slice_start_line <= location.start.line <= self.slice_end_line):
            return cst.RemoveFromParent()
        return updated_node

    def leave_Else(self, original_node: Else, updated_node: Else) -> cst.Else:
        """
        Parameters
        ----------
        original_node: cst.Else
            Original if node in AST 

        updated_node: cst.Else
            Update node in AST

        Returns
        ----------
        cst.Else
            Returns removing command if the original Else node is in slicing range and not in lines_to_keep list,
            otherwise returns the updated_node     
        """
        location = self.get_metadata(PositionProvider, original_node)
        if (self.slice_start_line <= location.start.line <= self.slice_end_line):
            for i in range(location.start.line, location.end.line + 1):
                if i in self.lines_to_keep:
                    return updated_node
            return cst.RemoveFromParent()
        return updated_node

    def leave_SimpleStatementLine(self, original_node: SimpleStatementLine, updated_node: SimpleStatementLine) -> BaseStatement:
        """
        Parameters
        ----------
        original_node: cst.SimpleStatementLine
            Original if node in AST 

        updated_node: cst.SimpleStatementLine
            Update node in AST

        Returns
        ----------
        cst.SimpleStatementLine
            Returns removing command if the original SimpleStatementLine node is in slicing range and not in lines_to_keep list,
            otherwise returns the updated_node     
        """
        location = self.get_metadata(PositionProvider, original_node)
        if (location.start.line not in self.lines_to_keep) and (self.slice_start_line <= location.start.line <= self.slice_end_line):
            return cst.RemoveFromParent()
        return updated_node

class CommentFinder(cst.CSTVisitor):
    """
    This class finds the line number which contains a specific comment
    """
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider
    )

    def __init__(self, target_comment):
        """
        Parameters
        ----------
        target_comment: str
            The comment that we aim to find its line number
        """
        self.target_comment = target_comment
        self.line_number = -1

    def visit_Comment(self, node: cst.Comment) -> None:
        """ We visit every comment node and if it contains the specified comment, we set the line_number to its line number
        
        Parameters
        ----------
        node: cst.Comment
            The node in AST that is a comment

        Returns
        ----------
        None   
        """
        if self.target_comment in node.value:
            location = self.get_metadata(PositionProvider, node)
            self.line_number = location.start.line

def remove_lines(code: str, lines_to_keep: List[int], slice_start_line: int, slice_end_line: int) -> str:
    """ This method accepts a code and an array of lines which refers to the lines that should be kept, and
    returns the new code after traversing the AST and removing the specified lines. 
        
    Parameters
    ----------
    code: str
        The code that should be sliced

    lines_to_keep: List[int]    
        A list which specifies which lines should be keept in the new code

    slice_start_line: int 
        The line number which specifies the start range of slicing
        
    slice_end_line: int   
        The line number which specifies the end range of slicing 

    Returns
    ----------
    str
        The new code that is truncated by the 
    ----------
    None   
    """
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = RemoveLines(
        lines_to_keep, slice_start_line, slice_end_line)
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code
