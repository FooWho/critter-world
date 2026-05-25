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
    ast = AbstractSyntaxTree(
        Parser(Lexer().tokenize("nearby[3] = 1 --> wait;")).parse()
    )
    print(ast.nodeCount)

    lexer = Lexer()
    parser = Parser(lexer.tokenize("--(--(---0)) = 5 --> wait;"))
    program = parser.parse()

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

    mutator = Mutator(ast)
    # mutator.faultInjection(ast)

    if mutator.mutate(1):
        print(str(ast.rootNode))
        # pass


if __name__ == "__main__":
    main()
