from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from abstractSyntaxTree import Relation
from typing import TYPE_CHECKING


def main():
    lexer = Lexer()
    tokens = lexer.tokenize('(1 + 5) * 6 <= 10 --> eat;')
    parser = Parser(tokens)

    try:
        parser.parseProgram()
    except CritterParseError as cpe:
        print(f'{cpe}')

if __name__ == "__main__":
    main()
