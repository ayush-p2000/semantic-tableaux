from operator_rules import And, Or, Not, Implies


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
        if isinstance(formula.operand, And):
            left_child = node.add_child(Not(formula.operand.left))
            right_child = node.add_child(Not(formula.operand.right))
            return left_child, right_child
        elif isinstance(formula.operand, Or):
            node.add_child(Not(formula.operand.left))
            node.add_child(Not(formula.operand.right))
        elif isinstance(formula.operand, Not):
            node.add_child(formula.operand.operand)
        elif isinstance(formula.operand, Implies):
            node.add_child(formula.operand.left)
            node.add_child(Not(formula.operand.right))
    elif isinstance(formula, Implies):
        left_child = node.add_child(Not(formula.left))
        right_child = node.add_child(formula.right)
        return left_child, right_child
    return None, None


def build_tableaux(root):
    stack = [root]
    while stack:
        node = stack.pop()
        left, right = expand(node)
        if left:
            stack.append(left)
        if right:
            stack.append(right)
