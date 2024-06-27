import re


class Formula:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

    def __repr__(self):
        if self.left and self.right:
            return f"({self.left} {self.value} {self.right})"
        elif self.left:
            return f"({self.value} {self.left})"
        else:
            return self.value


def parse_formula(input_str):
    # Remove spaces for easier parsing
    input_str = re.sub(r'\s+', '', input_str)

    def parse_expression(expression):
        # Handle parentheses
        if expression[0] == '(' and expression[-1] == ')':
            expression = expression[1:-1]

        # Logical operators precedence
        operators = ['<->', '->', '|', '&']
        for op in operators:
            parts = expression.split(op)
            if len(parts) > 1:
                left = parse_expression(parts[0])
                right = parse_expression(op.join(parts[1:]))
                formula = Formula(op)
                formula.left = left
                formula.right = right
                return formula

        # Handle NOT operator
        if expression[0] == '~':
            subformula = parse_expression(expression[1:])
            formula = Formula('~')
            formula.left = subformula
            return formula

        # Handle variables
        return Formula(expression)

    return parse_expression(input_str)


class Node:
    def __init__(self, formula, parent=None):
        self.formula = formula
        self.parent = parent
        self.children = []
        self.closed = False

    def __repr__(self):
        return f"Node({self.formula}, closed={self.closed})"


def expand_node(node):
    formula = node.formula
    if formula.value == '&':
        # Conjunction: Both parts must be true
        left_child = Node(formula.left, node)
        right_child = Node(formula.right, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '|':
        # Disjunction: At least one part must be true
        left_child = Node(formula.left, node)
        right_child = Node(formula.right, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '->':
        # Implication: If left is true, right must be true
        not_left = Formula('~')
        not_left.left = formula.left
        left_child = Node(not_left, node)
        right_child = Node(formula.right, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '<->':
        # Biconditional: Both parts must be equivalent
        left_imp_right = Formula('->')
        left_imp_right.left = formula.left
        left_imp_right.right = formula.right
        right_imp_left = Formula('->')
        right_imp_left.left = formula.right
        right_imp_left.right = formula.left
        left_child = Node(left_imp_right, node)
        right_child = Node(right_imp_left, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '~':
        # Negation: Handle negation of conjunction, disjunction, implication, and double negation
        if formula.left.value == '&':
            # Negation of a conjunction: at least one part must be false
            not_left = Formula('~')
            not_left.left = formula.left.left
            not_right = Formula('~')
            not_right.left = formula.left.right
            node.children.append(Node(not_left, node))
            node.children.append(Node(not_right, node))
        elif formula.left.value == '|':
            # Negation of a disjunction: both parts must be false
            not_left = Formula('~')
            not_left.left = formula.left.left
            not_right = Formula('~')
            not_right.left = formula.left.right
            node.children.append(Node(not_left, node))
            node.children.append(Node(not_right, node))
        elif formula.left.value == '->':
            # Negation of an implication: left is true and right is false
            left = formula.left.left
            not_right = Formula('~')
            not_right.left = formula.left.right
            node.children.append(Node(left, node))
            node.children.append(Node(not_right, node))
        elif formula.left.value == '<->':
            # Negation of a biconditional: parts are not equivalent
            not_left_imp_right = Formula('~')
            left_imp_right = Formula('->')
            left_imp_right.left = formula.left.left
            left_imp_right.right = formula.left.right
            not_left_imp_right.left = left_imp_right

            not_right_imp_left = Formula('~')
            right_imp_left = Formula('->')
            right_imp_left.left = formula.left.right
            right_imp_left.right = formula.left.left
            not_right_imp_left.left = right_imp_left

            node.children.append(Node(not_left_imp_right, node))
            node.children.append(Node(not_right_imp_left, node))
        elif formula.left.value == '~':
            # Double negation elimination
            node.children.append(Node(formula.left.left, node))


def is_contradiction(node):
    literals = set()
    current = node
    while current:
        if isinstance(current.formula, Formula):
            if current.formula.value == '~' and isinstance(current.formula.left, Formula):
                literal = current.formula.left.value
                if literal in literals:
                    return True
                literals.add(f"~{literal}")
            elif not current.formula.left and not current.formula.right:
                literal = current.formula.value
                if f"~{literal}" in literals:
                    return True
                literals.add(literal)
        current = current.parent
    return False


def check_satisfiability(root):
    def is_branch_satisfiable(node):
        if node.closed:
            return False
        if not node.children:
            return True
        if node.formula.value == '&':
            return all(is_branch_satisfiable(child) for child in node.children)
        else:  # '|', '->', '<->', '~'
            return any(is_branch_satisfiable(child) for child in node.children)

    stack = [root]
    while stack:
        node = stack.pop()
        print(f"Expanding node: {node}")
        if node.closed:
            continue
        expand_node(node)
        for child in node.children:
            if is_contradiction(child):
                child.closed = True
                print(f"Contradiction found at node: {child}")
            else:
                stack.append(child)

        # Check if the current node should be closed based on its children
        if node.formula.value == '&' and any(child.closed for child in node.children):
            node.closed = True
        elif node.formula.value in {'|', '->', '<->', '~'} and all(child.closed for child in node.children):
            node.closed = True

    return is_branch_satisfiable(root)


def main():
    input_str = "(p -> (q & r))"
    formula = parse_formula(input_str)
    root = Node(formula)
    satisfiable = check_satisfiability(root)
    if satisfiable:
        print("The formula is satisfiable.")
    else:
        print("The formula is not satisfiable.")


if __name__ == "__main__":
    main()
