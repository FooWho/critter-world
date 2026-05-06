from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from typing import TYPE_CHECKING

def main():
    lexer = Lexer()
    tokens = lexer.tokenize('5 * --3 / 4')
    parser = Parser(tokens)
    ast = parser.parse()
    for child in ast.getRoot():
        print(f'{child}')
    print('Ok')


if __name__ == "__main__":
    main()
