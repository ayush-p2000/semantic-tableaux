from operator_rules import Not


def is_open_branch(node):
    # Collect all formulas up to the root
    formulas = set()
    current = node
    while current:
        if isinstance(current.formula, Not):
            if current.formula.operand in formulas:
                return False
        else:
            if Not(current.formula) in formulas:
                return False
        formulas.add(current.formula)
        current = current.parent
    return True


def check_satisfiability(root):
    stack = [root]
    while stack:
        node = stack.pop()
        if not node.children:  # Leaf node
            if is_open_branch(node):
                return True
        else:
            stack.extend(node.children)
    return False
