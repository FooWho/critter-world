from lexer import Lexer
from schemas import Token
from parser import Parser
from typing import TYPE_CHECKING


def main():
    lexer = Lexer()
    tokens = lexer.tokenize('1 <= 10 --> eat;')
    parser = Parser(tokens)
    parser.parseProgram()

if __name__ == "__main__":
    main()
