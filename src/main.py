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
import json, sys


def main():
    with open("parameters.json", "r") as file:
        data = json.load(file)

    if len(sys.argv) > 1:
        parentFile = sys.argv[1]
    else:
        parentFile = "daddy.crtr"
    if len(sys.argv) > 2:
        childFile = sys.argv[2]
    else:
        childFile = "baby.crtr"
    if len(sys.argv) > 3:
        mutations = int(sys.argv[3])
    else:
        mutations = 0

    with open(parentFile, "r", encoding="utf-8") as file:
        content = file.read()

    lexer = Lexer()
    tokens = lexer.tokenize(content)
    parser = Parser(tokens)
    daddy = AbstractSyntaxTree(parser.parse())

    baby = AbstractSyntaxTree(daddy.copyProgram())
    mutator = Mutator(baby, data.get("MUTATION_PROBABILITY"))
    mutator.mutate(mutations)

    with open(childFile, "w", encoding="utf-8") as file:
        file.write(str(baby.rootNode))


if __name__ == "__main__":
    main()
