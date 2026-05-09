from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from typing import TYPE_CHECKING

def main():
    lexer = Lexer()
    tokens = lexer.tokenize('{{4+2 < 5 mod mem[nearby[6]]} or {3 != 5 and 4 > 6}} and {{4 < smell}}')
    parser = Parser(tokens)
    try:
        ast = parser.parse()
        for child in ast.getRoot():
            print(f'{child}')
    except CritterParseError as cpe:
        print(cpe)

    print('Ok')


if __name__ == "__main__":
    main()
