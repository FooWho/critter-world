from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from typing import TYPE_CHECKING

def main():
    lexer = Lexer()
    tokens = lexer.tokenize('3 * mem[4 * mem[8]] * 5 * 6')
    parser = Parser(tokens)
    ast = parser.parse()
    for child in ast.getRoot():
        print(f'{child}')
    print('Ok')


if __name__ == "__main__":
    main()
