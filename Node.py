class Node:
    def __init__(self, formula, parent=None):
        self.formula = formula
        self.parent = parent
        self.children = []

    def add_child(self, formula):
        child = Node(formula, self)
        self.children.append(child)
        return child
