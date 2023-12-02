from typing import List
import libcst as cst
from libcst._nodes.statement import SimpleStatementLine, BaseStatement, For, If, Else, While
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)
import libcst.matchers as m
from libcst.metadata import PositionProvider

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

def negate_odd_ifs(code: str) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = OddIfNegation()
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def remove_lines(code: str, lines_to_keep: List[int]) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = RemoveLines(lines_to_keep)
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def get_slicing_criterion_line(source_path: str, comment: str) -> int:
    with open(source_path, "r") as file:
        code = file.read()
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    comment_finder = CommentFinder(comment)
    _ = wrapper.visit(comment_finder)
    return comment_finder.line_number