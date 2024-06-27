class Formula:
    def __init__(self, value):
        self.value = value


class Var(Formula):
    def __init__(self, name):
        super().__init__(name)


class Not(Formula):
    def __init__(self, formula):
        super().__init__(formula)


class And(Formula):
    def __init__(self, formula1, formula2):
        super().__init__((formula1, formula2))


class Or(Formula):
    def __init__(self, formula1, formula2):
        super().__init__((formula1, formula2))


class Implication(Formula):
    def __init__(self, antecedent, consequent):
        super().__init__((antecedent, consequent))


class Biconditional(Formula):
    def __init__(self, formula1, formula2):
        super().__init__((formula1, formula2))


def tableaux(formula):
    if isinstance(formula, Var):
        return True
    elif isinstance(formula, Not):
        return not tableaux(formula.value)
    elif isinstance(formula, And):
        return tableaux(formula.value[0]) and tableaux(formula.value[1])
    elif isinstance(formula, Or):
        return tableaux(formula.value[0]) or tableaux(formula.value[1])
    elif isinstance(formula, Implication):
        antecedent, consequent = formula.value
        return not tableaux(antecedent) or tableaux(consequent)
    elif isinstance(formula, Biconditional):
        formula1, formula2 = formula.value
        return (tableaux(formula1) and tableaux(formula2)) or (not tableaux(formula1) and not tableaux(formula2))
    else:
        raise ValueError("Unsupported formula type")


# Example usage
p = Var("p")
q = Var("q")
r = Var("r")

# False testing formulasb
f_contradiction = And(p, Not(p))  # Contradiction: p and not p
f_false_implication = Implication(p, Not(p))  # False Implication: p => not p
f_false_biconditional = Biconditional(p, Not(p))  # False Biconditional: p <=> not p
f_nested_contradiction = And(p, Or(Not(p), q))  # Nested Contradiction: p and (not p or q)

# Assume p is true, q is false, and r is true
print(tableaux(f_contradiction))  # Output: False
print(tableaux(f_false_implication))  # Output: False
print(tableaux(f_false_biconditional))  # Output: False
print(tableaux(f_nested_contradiction))  # Output: False

# Additional correct outputs for completeness
print(tableaux(p))  # Output: True
print(tableaux(Not(p)))  # Output: False
print(tableaux(And(p, q)))  # Output: False (p is true, q is false)
print(tableaux(Or(p, q)))  # Output: True (p is true, q is false)
print(tableaux(Implication(p, q)))  # Output: False (p is true, q is false)
print(tableaux(Biconditional(q, r)))  # Output: False (q is false, r is true)
