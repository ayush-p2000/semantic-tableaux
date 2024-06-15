from operator_rules import Atom, And, Or, Not
from expanison import build_tableaux
from Node import Node
from justification import check_satisfiability

# Create a formula (A ∧ (¬B ∨ C))
A = Atom('A')
B = Atom('B')
C = Atom('C')
formula = And(A, And(Not(B), C))

# Build the tableaux
root = Node(formula)
build_tableaux(root)

# Check satisfiability
print("Satisfiable:" if check_satisfiability(root) else "Unsatisfiable")
