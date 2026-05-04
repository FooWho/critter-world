from __future__ import annotations
from typing import ClassVar, Iterable, Iterator, TYPE_CHECKING
from schemas import Token, CritterParseError, TokenLexeme, TermTuple, FactorTuple, TOKENS, SET_RELOPS, SET_ADDOPS, SET_MULOPS, SET_SENSORS 
from schemas import SET_FACTOR_INITIATOR, SET_FACTOR_TERMINATOR, SET_RULE_INITIATOR, SET_RULE_TERMINATOR, SET_CONDITION_INITIATOR, SET_CONDITION_TERMINATOR
from schemas import SET_CONJUNCTION_INITIATOR, SET_CONJUNCTION_TERMINATOR, SET_RELATION_INITIATOR, SET_RELATION_TERMINATOR
from abstractSyntaxTree import Program, Rule, Condition, Command, Conjunction, Relation, Expr, Term, Factor, Number, GroupedExpression

class Parser():
    def __init__(self, tokens: Iterator[Token]) -> None:
        self.tokens: Iterator[Token] = tokens
        self.current = next(self.tokens, Token(TOKENS.T_NONE, '', 0, 0))


    def getToken(self) -> Token:
        token = self.current
        self.current = next(self.tokens, Token(TOKENS.T_NONE, '', 0, 0))

        return token
    
    def peek(self) -> Token:
        return self.current
    
    def parseProgram(self) -> Program:
        program = Program()

        token = self.getToken()

        while token.tokenType != TOKENS.T_EOF:

            if token is self.peek():
                token = self.getToken()

            if token.tokenType not in SET_RULE_INITIATOR:
                raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected RULE. Read: {token.tokenType}:"{token.lexeme}"')
            
            rule = self.parseRule(token)
            program.addRule(rule)
     
            token = self.peek()

        return program
    
    def parseRule(self, token: Token) -> Rule:
        rule = Rule()
        condition = Condition()

        while token.tokenType != SET_RULE_TERMINATOR:

            if token is self.peek():
                token = self.getToken()

            if token.tokenType not in SET_CONDITION_INITIATOR:
                raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected CONDITION. Read: {token.tokenType}:"{token.lexeme}"')
            
            condition = self.parseCondition(token)



        command = self.parseCommand(token)

        return Rule(condition, command)
    
    def parseCondition(self, token: Token) -> Condition:
        condition: Condition = Condition()
        conjunctions: list[Conjunction] = []
        conjunction: Conjunction = Conjunction()

        while token.tokenType not in SET_CONDITION_TERMINATOR:

            if token is self.peek():
                token = self.getToken()

            if token.tokenType not in SET_CONJUNCTION_INITIATOR:
                raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected CONJUNCTION. Read: {token.tokenType}:"{token.lexeme}"')   

            conjunction = self.parseConjunction(token)
            condition.addConjunction(conjunction)

        return condition
    
    
    def parseCommand(self, token: Token) -> Command:
        command: Command = Command()

        return command
    
    def parseConjunction(self, token: Token) -> Conjunction:
        conjunction: Conjunction = Conjunction()
        relation: Relation = Relation()

        while token.tokenType not in SET_CONJUNCTION_TERMINATOR:
            if token is self.peek():
                token = self.getToken()

            if token.tokenType not in SET_RELATION_INITIATOR:
                raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected RELATION. Read: {token.tokenType}:"{token.lexeme}"') 

            relation = self.parseRelation(token)
            conjunction.addRelation(relation)

        return conjunction
    
    def parseRelation(self, token: Token) -> Relation:
        leftExpression: Expr
        relOp: TokenLexeme
        rightExpression: Expr
        relation = Relation()

        if token.tokenType == TOKENS.T_L_BRACE:
            pass
        else:
            leftExpression = self.parseExpression(token)
            token = self.getToken()
            relOp = TokenLexeme(token.tokenType, token.lexeme)
            token = self.getToken()
            rightExpression = self.parseExpression(token)     

            relation = Relation(leftExpression, relOp, rightExpression)
        print(f'{relation}')
        return relation
    
    def parseExpression(self, token: Token) -> Expr:
        expression: Expr = Expr()

        expression.setTerms(self.parseTerms(token))
        return expression
    
    def parseTerms(self, token: Token) -> list[TermTuple]:
        terms: list[TermTuple] = []
  
        while token.tokenType not in SET_RELOPS | {TOKENS.T_COMM, TOKENS.T_R_PAREN}:
            if token is self.peek():
                token = self.getToken()
            addOp: TokenLexeme = TokenLexeme(TOKENS.T_NONE, '')
            if token.tokenType in {TOKENS.T_PLUS, TOKENS.T_MINUS}:
                addOp = TokenLexeme(token.tokenType, token.lexeme)
                token = self.getToken()
            factorTupleList = self.parseFactors(token)
            term = Term(factorTupleList)
            terms.append(TermTuple(addOp, term))
            token = self.peek()
        
        return terms
    
    def parseFactors(self, token: Token) -> list[FactorTuple]:
        number: Number
        groupedExpression: GroupedExpression
        mulOp: TokenLexeme = TokenLexeme(TOKENS.T_NONE, '')
        factors:list[FactorTuple] = []

        while token.tokenType not in SET_FACTOR_TERMINATOR:
            if token is self.peek():
                # Our look-ahead says we are still here, advance the cursor
                token = self.getToken()
            # Parsing a factor, if it is not the first, it will have a leading mulOp, otherwise it is a syntax error
            if token.tokenType in SET_MULOPS and factors:
                # We are looking at a mulOp and this is not the first factor
                mulOp = TokenLexeme(token.tokenType, token.lexeme)
                token = self.getToken()
            if token.tokenType not in SET_FACTOR_INITIATOR:
                raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected FACTOR. Read: {token.tokenType}:"{token.lexeme}"')
            # We should have a T_NUMBER, a T_MEM, a T_L_PAREN, a T_MINUS, or token ∈ {SET_SENSORS}
            match token.tokenType:
                case TOKENS.T_NUMBER:
                    number = self.parseNumber(token)
                    factors.append(FactorTuple(mulOp, number))
                    token = self.peek()
                case TOKENS.T_MEM:
                    pass
                case TOKENS.T_L_PAREN:
                    # We should be reading a grouped expression
                    groupedExpression = self.parseGroupedExpression(token)
                    factors.append(FactorTuple(mulOp, groupedExpression))
                    token = self.peek()
                case TOKENS.T_MINUS:
                    pass
                case val if val in SET_SENSORS:
                    pass 
                case _:
                    raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected FACTOR. Read: {token.tokenType}:"{token.lexeme}"')         
                
        return factors
    
    def parseNumber(self, token: Token) -> Number:
        num: Number

        if token.tokenType != TOKENS.T_NUMBER:
            raise CritterParseError('Error!')
        else:    
            return Number(TokenLexeme(token.tokenType, token.lexeme))
    
    def parseGroupedExpression(self, token: Token) -> GroupedExpression:
        expr: Expr
        token = self.getToken()
        expr = self.parseExpression(token)
        token = self.peek()
        if token.tokenType != TOKENS.T_R_PAREN:
            raise CritterParseError(f'Error on line {token.line} at position {token.column}: Expected ")". Read: {token.tokenType}:"{token.lexeme}"')
        token = self.getToken()
        return GroupedExpression(expr)

