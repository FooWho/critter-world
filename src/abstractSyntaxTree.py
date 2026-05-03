from __future__ import annotations
from typing import ClassVar, Iterable, TYPE_CHECKING
from schemas import TokenLexeme, FactorTuple, TermTuple, TOKENS

class AbstractSyntaxTree():

    def __init__(self, rootNode: ASTNode|None = None) -> None:
        self.rootNode: ASTNode = rootNode or ASTNode()


class ASTNode():
    _children: ClassVar[tuple[str, ...]] = ()
    
    def __iter__(self) -> Iterable[ASTNode]:
        for fieldName in self._children:
            value = getattr(self, fieldName, None)
            if isinstance(value, list):
                yield from (item for item in value 
                            if isinstance(item, ASTNode))
            elif isinstance(value, ASTNode):
                yield value

class Program(ASTNode):
    _children: ClassVar[tuple[str]] = ('rules',)

    def __init__(self, rules: list[Rule]|None = None) -> None:
        self.rules: list[Rule] = rules or []

    def addRule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def setRules(self, rules: list[Rule]) -> None:
        self.rules = rules


class Rule(ASTNode):
    _children: ClassVar[tuple[str, str]] = ('condition', 'command')
    
    def __init__(self, condition: Condition|None = None, command: Command|None = None) -> None:
        self.condition: Condition = condition or Condition()
        self.command: Command = command or Command()

    def setRule(self, rule: Rule) -> None: 
        self.condition = rule.condition 
        self.command = rule.command

class Condition(ASTNode):
    _children: ClassVar[tuple[str]] = ('conjunctions',)
    
    def __init__(self, conjunctions: list[Conjunction]|None = None) -> None:
        self.conjunctions: list[Conjunction] = conjunctions or []

    def addConjunction(self, conjunction: Conjunction) -> None:
        self.conjunctions.append(conjunction)

    def setConjunctions(self, conjunctions: list[Conjunction]) -> None:
        self.conjunctions = conjunctions

class Command(ASTNode):
    pass

class Conjunction(ASTNode):
    _children: ClassVar[tuple[str]] = ('relations',)

    def __init(self, relations: list[Relation]|None = None) -> None:
        self.relations: list[Relation] = relations or []

    def addRelation(self, relation: Relation) -> None:
        self.relations.append(relation)

    def setRelations(self, relations: list[Relation]) -> None:
        self.relations = relations

class Relation(ASTNode):
    _children: ClassVar[tuple[str, str, str]] = ('leftExpr', 'relOp', 'rightExpr')

    def __init__(self, leftExpr: Expr|None = None, 
                 rightExpr: Expr|None = None, 
                 relOp: TokenLexeme|None = None) -> None:
        
        self.leftExpr: Expr = leftExpr or Expr()
        self.relOp: TokenLexeme = relOp or TokenLexeme(TOKENS.T_NONE, '')
        self.rightExpr: Expr = rightExpr or Expr()  

    def __repr__(self) -> str: 
        return str(self.leftExpr) + ' ' + self.relOp.lexeme + ' ' + str(self.rightExpr)
    
class Expr(ASTNode):
    _children: ClassVar[tuple[str]] = ('terms',)

    def __init__(self, terms: list[TermTuple]|None = None) -> None:
        self.terms: list[TermTuple] = terms or []

    def __repr__(self) -> str:
        tmp = str(self.terms[0].term)
        for term in self.terms[1:]:
            tmp += ' ' + term.addOp.lexeme + ' ' + str(term.term)
        return tmp
    
    def addTerm(self, term: TermTuple) -> None:
        self.terms.append(term)

    def setTerms(self, terms: list[TermTuple]) -> None:
        self.terms:list[TermTuple] = terms


class Term(ASTNode):
    _children: ClassVar[tuple[str]] = ('factors',)

    def __init__(self, factors: list[FactorTuple]|None = None) -> None:
        self.factors: list[FactorTuple] = factors or []

    def __repr__(self) -> str:
        tmp = str(self.factors[0].factor)
        for factor in self.factors[1:]:
            tmp += ' ' + factor.mulOp.lexeme + ' '
            tmp += str(factor.factor)
        return tmp

    def addFactor(self, factor: FactorTuple) -> None:
        self.factors.append(factor)

    def setFactors(self, factors: list[FactorTuple]) -> None:
        self.factors = factors


class Factor(ASTNode):
    _children: ClassVar[tuple[str]] = ('factor',)

    def __init__(self, factor: Number|None = None) -> None:
        self.factor = factor or Number()

    def __repr__(self) -> str:
        return str(self.factor)
    
    def createNumber(self) -> Number:

        return Number()


class Number(ASTNode):
    _children: ClassVar[tuple[str]] = ('number',)

    def __init__(self, number: TokenLexeme|None = None) -> None:
        self.number:TokenLexeme = number or TokenLexeme(TOKENS.T_NONE, '')

    def __repr__(self) -> str:
        return self.number.lexeme
        


