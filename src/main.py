from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from abstractSyntaxTree import Program
from typing import TYPE_CHECKING

def main():
    lexer = Lexer()
    tokens = lexer.tokenize('{7 = (2 * 4) or 4 = 3} and {1 = 1 or 0 = 1}')
    parser = Parser(tokens)
    ast = Program()
    try:
        ast = parser.parse()
    except CritterParseError as cpe:
        print(cpe)

    print(f'{ast.getRoot()} := {ast.getRoot().evaluate()}')
    #print(f'{ast.getRoot()}')
    print('Ok')


if __name__ == "__main__":
    main()
