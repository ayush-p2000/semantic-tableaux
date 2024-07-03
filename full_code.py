import re
import pydot
import os


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

    def is_variable(self):
        return not self.left and not self.right and self.value.isalpha()


def parse_formula(input_str):
    input_str = re.sub(r'\s+', '', input_str)

    def parse_expression(expression):
        if expression[0] == '(' and expression[-1] == ')':
            expression = expression[1:-1]

        operators = ['<->', '->', '&', '|']
        for op in operators:
            parts = split_expression(expression, op)
            if len(parts) > 1:
                if op == '&':
                    result = parse_expression(parts[0])
                    for part in parts[1:]:
                        new_formula = Formula('&')
                        new_formula.left = result
                        new_formula.right = parse_expression(part)
                        result = new_formula
                    return result
                elif op == '<->':
                    left = parse_expression(parts[0])
                    right = parse_expression(parts[1])
                    formula = Formula('<->')
                    formula.left = left
                    formula.right = right
                    return formula
                else:
                    left = parse_expression(parts[0])
                    right = parse_expression(op.join(parts[1:]))
                    formula = Formula(op)
                    formula.left = left
                    formula.right = right
                    return formula

        if expression[0] == '~':
            subformula = parse_expression(expression[1:])
            formula = Formula('~')
            formula.left = subformula
            return formula

        return Formula(expression)

    return parse_expression(input_str)


def split_expression(expression, operator):
    parts = []
    depth = 0
    current_part = []
    i = 0
    while i < len(expression):
        if expression[i] == '(':
            depth += 1
        elif expression[i] == ')':
            depth -= 1
        if depth == 0 and expression[i:i + len(operator)] == operator:
            parts.append(''.join(current_part))
            current_part = []
            i += len(operator)
            continue
        current_part.append(expression[i])
        i += 1
    parts.append(''.join(current_part))
    return parts

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
        left_child = Node(formula.left, node)
        right_child = Node(formula.right, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '|':
        left_child = Node(formula.left, node)
        right_child = Node(formula.right, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '->':
        not_left = Formula('~')
        not_left.left = formula.left
        left_child = Node(not_left, node)
        right_child = Node(formula.right, node)
        node.children.append(left_child)
        node.children.append(right_child)
    elif formula.value == '<->':
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
        if formula.left.value == '&':
            not_left = Formula('~')
            not_left.left = formula.left.left
            not_right = Formula('~')
            not_right.left = formula.left.right
            node.children.append(Node(not_left, node))
            node.children.append(Node(not_right, node))
        elif formula.left.value == '|':
            not_left = Formula('~')
            not_left.left = formula.left.left
            not_right = Formula('~')
            not_right.left = formula.left.right
            node.children.append(Node(not_left, node))
            node.children.append(Node(not_right, node))
        elif formula.left.value == '->':
            left = formula.left.left
            not_right = Formula('~')
            not_right.left = formula.left.right
            node.children.append(Node(left, node))
            node.children.append(Node(not_right, node))
        elif formula.left.value == '<->':
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
            node.children.append(Node(formula.left.left, node))


def is_contradiction(node):
    literals = set()
    current = node
    while current:
        if isinstance(current.formula, Formula):
            if current.formula.value == '~':
                if isinstance(current.formula.left,
                              Formula) and not current.formula.left.left and not current.formula.left.right:
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
        else:
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

        if node.formula.value == '&' and any(child.closed for child in node.children):
            node.closed = True
        elif node.formula.value in {'|', '->', '<->', '~'} and all(child.closed for child in node.children):
            node.closed = True

    return is_branch_satisfiable(root)


def expand_and_visualize(node, graph, parent_node=None):
    expand_node(node)
    current_node = pydot.Node(str(node.formula), shape='ellipse', style='filled', fillcolor='lightblue')
    graph.add_node(current_node)

    if parent_node is not None:
        edge = pydot.Edge(parent_node, current_node)
        graph.add_edge(edge)

    for child in node.children:
        expand_and_visualize(child, graph, current_node)


def visualize_tree(root):
    graph = pydot.Dot(graph_type='graph')
    expand_and_visualize(root, graph)
    graph.write_png('tree_diagram.png')


# Main function to parse, build tree, and visualize
def main():
    # Set Graphviz path (example path)
    os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

    input_str = "(p -> q) & (~q -> ~p) & ~(p <-> q)"
    formula = parse_formula(input_str)
    print(formula)
    root = Node(formula)

    # Visualize the tree
    visualize_tree(root)

    print(f"Testing: {input_str}")
    root = Node(formula)
    satisfiable = check_satisfiability(root)
    if satisfiable:
        print("The formula is satisfiable.")
    else:
        print("The formula is not satisfiable.")


if __name__ == "__main__":
    main()
