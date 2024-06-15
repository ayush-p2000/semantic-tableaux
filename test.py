class Formula:
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(frozenset(self.__dict__.items()))

class And(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} ∧ {self.right})"

class Or(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} ∨ {self.right})"

class Not(Formula):
    def __init__(self, operand):
        self.operand = operand

    def __repr__(self):
        return f"¬{self.operand}"

class Implies(Formula):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} → {self.right})"

class Atom(Formula):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

class Node:
    def __init__(self, formula, parent=None):
        self.formula = formula
        self.parent = parent
        self.children = []

    def add_child(self, formula):
        child = Node(formula, self)
        self.children.append(child)
        return child

def expand(node):
    formula = node.formula
    if isinstance(formula, And):
        node.add_child(formula.left)
        node.add_child(formula.right)
    elif isinstance(formula, Or):
        left_child = node.add_child(formula.left)
        right_child = node.add_child(formula.right)
        return left_child, right_child
    elif isinstance(formula, Not):
        operand = formula.operand
        if isinstance(operand, And):
            node.add_child(Not(operand.left))
            node.add_child(Not(operand.right))
        elif isinstance(operand, Or):
            left_child = node.add_child(Not(operand.left))
            right_child = node.add_child(Not(operand.right))
            return left_child, right_child
        elif isinstance(operand, Not):
            node.add_child(operand.operand)
        elif isinstance(operand, Implies):
            node.add_child(operand.left)
            node.add_child(Not(operand.right))
    elif isinstance(formula, Implies):
        left_child = node.add_child(Not(formula.left))
        right_child = node.add_child(formula.right)
        return left_child, right_child
    return None, None

def build_tableaux(root):
    stack = [root]
    while stack:
        node = stack.pop()
        print(f"Expanding node with formula: {node.formula}")
        left, right = expand(node)
        if left:
            stack.append(left)
        if right:
            stack.append(right)

def is_open_branch(node):
    formulas = set()
    negations = set()
    current = node
    while current:
        if isinstance(current.formula, Not):
            negated_formula = current.formula.operand
            if negated_formula in formulas:
                return False  # Found a contradiction
            negations.add(negated_formula)
        else:
            if current.formula in negations:
                return False  # Found a contradiction
            formulas.add(current.formula)
        current = current.parent
    return True  # No contradictions found, branch is open
def check_satisfiability(root):
    stack = [root]
    open_branches = 0
    while stack:
        node = stack.pop()
        if not node.children:  # Leaf node
            if is_open_branch(node):
                open_branches += 1  # Count open branches
        else:
            stack.extend(node.children)
    return open_branches > 0  # If there's at least one open branch, the formula is satisfiable

# Example usage
if __name__ == "__main__":
    # Create a formula A ∧ ¬A
    A = Atom('A')
    formula = And(A, Not(A))

    # Build the tableaux
    root = Node(formula)
    build_tableaux(root)

    # Check satisfiability
    result = check_satisfiability(root)
    print("Satisfiable" if result else "Unsatisfiable")
