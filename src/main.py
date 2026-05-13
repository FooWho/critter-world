from lexer import Lexer
from schemas import CritterParseError
from parser import Parser
from abstractSyntaxTree import AbstractSyntaxTree, Program, Rule, Command, CommandBlock
from typing import TYPE_CHECKING

def main():
    lexer = Lexer()
    
    with open('test/critter1.crtr', 'r', encoding='utf-8') as file:
        content = file.read() 
    tokens = lexer.tokenize(content)
    parser = Parser(tokens)
    Program()
    try:
        ast = AbstractSyntaxTree(parser.parse())
    except CritterParseError as cpe:
        print(cpe)
        exit(1)
    print(str(ast.getRoot()))
    print('Ok')


if __name__ == "__main__":
    main()
