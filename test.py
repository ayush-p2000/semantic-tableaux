from mathesis.grammars import BasicGrammar

grammar = BasicGrammar(symbols={"conditional": "⊃"})

fml = grammar.parse("¬(A⊃C)")

print(fml, repr(fml))