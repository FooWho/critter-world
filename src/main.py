from lexer import Lexer
from schemas import CritterParseError, Token, TOKENS
from parser import Parser
from abstractSyntaxTree import (
    AbstractSyntaxTree,
    Program,
    Rule,
    Command,
    Number,
    MemNode,
    ExpressionNode,
    countNodes,
)
from typing import TYPE_CHECKING
from mutator import Mutator


def main():
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
    print(str(ast.getRoot()))
    print("* Ok *")
    print(f"Nodes: {ast.getNodeCount()}")

    mutator = Mutator()
    # mutator.faultInjection(ast)

    if mutator.mutate(ast, 1):
        print(str(ast.getRoot()))


if __name__ == "__main__":
    main()
