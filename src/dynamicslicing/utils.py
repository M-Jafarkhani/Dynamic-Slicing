from typing import List
import libcst as cst
from libcst._flatten_sentinel import FlattenSentinel
from libcst._nodes.statement import SimpleStatementLine, BaseStatement, For, If, Else, While
from libcst._removal_sentinel import RemovalSentinel
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)
import libcst.matchers as m


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
