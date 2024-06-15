class Formula:
    pass


class And(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Or(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Not(Formula):
    def __init__(self, operand):
        self.operand = operand


class Implies(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right


class Atom(Formula):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name
