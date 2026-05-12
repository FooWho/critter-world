from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from abstractSyntaxTree import Program, Rule, Command, CommandBlock
from typing import TYPE_CHECKING

def main():
    lexer = Lexer()
    with open('test/critter1.crtr', 'r', encoding='utf-8') as file:
        content = file.read() 
    tokens = lexer.tokenize(content)
    parser = Parser(tokens)
    ast = Program()
    try:
        ast = parser.parse()
    except CritterParseError as cpe:
        print(cpe)
    print(str(ast))
    print('Ok')


if __name__ == "__main__":
    main()
