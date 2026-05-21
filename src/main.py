from __future__ import annotations
from typing import cast
from lexer import Lexer
from schemas import CritterParseError, Token, TOKENS
from parser import Parser
from abstractSyntaxTree import (
    AbstractSyntaxTree,
    ASTNode,
    Program,
    BooleanOperator,
    BinaryOperator,
    UnaryOperator,
    LogicalOperator,
    RelationalOperator,
    Action,
    Update,
    Rule,
    Command,
    Number,
    MemNode,
    ExpressionNode,
    countNodes,
)

from mutator import Mutator


def main():
    number = Number(value=-5)
    number = cast(UnaryOperator, number)
    number.operand.value = 5

    lexer = Lexer()
    with open("test/critter1.crtr", "r", encoding="utf-8") as file:
        lines = file.readlines()
    lineContent = lines[8:]
    content = "".join(lineContent)
    tokens = lexer.tokenize(content)
    parser = Parser(tokens)
    Program()
    try:
        ast = AbstractSyntaxTree(parser.parse())
    except CritterParseError as cpe:
        print(cpe)
        exit(1)
    print(str(ast.rootNode))
    print("* Ok *")
    print(f"Nodes: {ast.nodeCount}")

    mutator = Mutator()
    # mutator.faultInjection(ast)

    if mutator.mutate(ast, 1):
        print(str(ast.rootNode))
        # pass


if __name__ == "__main__":
    main()
