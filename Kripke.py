from dataclasses import dataclass
from typing import List, Tuple, Set, Dict

import pydot

@dataclass
class Formula:
    pass

@dataclass
class Atom(Formula):
    name: str

@dataclass
class Not(Formula):
    formula: Formula

@dataclass
class And(Formula):
    conjuncts: List[Formula]

@dataclass
class Or(Formula):
    disjuncts: List[Formula]

@dataclass
class Implies(Formula):
    left: Formula
    right: Formula

@dataclass
class Box(Formula):
    formula: Formula

@dataclass
class Diamond(Formula):
    formula: Formula

Branch = List[Tuple[bool, str, Formula]]

def apply_rule(sign: bool, prefix: str, formula: Formula, expanded_prefixes: set) -> List[
    List[Tuple[bool, str, Formula]]]:
    print(f"Applying rule to: {'T' if sign else 'F'} {prefix} {formula}")
    if isinstance(formula, Atom):
        return []  # No expansion needed for atomic formulas
    elif isinstance(formula, Not):
        return [[(not sign, f"{prefix}.1", formula.formula)]]
    elif isinstance(formula, And):
        if sign:
            return [[(True, f"{prefix}.{i + 1}", conj) for i, conj in enumerate(formula.conjuncts)]]
        else:
            return [[(False, f"{prefix}.{i + 1}", conj)] for i, conj in enumerate(formula.conjuncts)]
    elif isinstance(formula, Or):
        if sign:
            return [[(True, f"{prefix}.{i + 1}", disj)] for i, disj in enumerate(formula.disjuncts)]
        else:
            return [[(False, f"{prefix}.{i + 1}", disj) for i, disj in enumerate(formula.disjuncts)]]
    elif isinstance(formula, Implies):
        if sign:
            return [[(False, f"{prefix}.1", formula.left)], [(True, f"{prefix}.2", formula.right)]]
        else:
            return [[(True, f"{prefix}.1", formula.left), (False, f"{prefix}.2", formula.right)]]
    elif isinstance(formula, Box):
        if sign:
            return [[(True, f"{prefix}.1", formula.formula)]] if (prefix, "Box") not in expanded_prefixes else []
        else:
            return [[(False, f"{prefix}.1", formula.formula)]] if (prefix, "Box") not in expanded_prefixes else []
    elif isinstance(formula, Diamond):
        if sign:
            return [[(True, f"{prefix}.1", formula.formula)]] if (prefix, "Diamond") not in expanded_prefixes else []
        else:
            return [[(False, f"{prefix}.1", formula.formula)]] if (prefix, "Diamond") not in expanded_prefixes else []
    raise ValueError(f"Unknown formula type: {type(formula)}")

def is_closed(branch: Branch) -> bool:
    positive_atoms = set()
    negative_atoms = set()
    for sign, prefix, formula in branch:
        if isinstance(formula, Atom):
            if sign:
                if formula.name in negative_atoms:
                    return True
                positive_atoms.add(formula.name)
            else:
                if formula.name in positive_atoms:
                    return True
                negative_atoms.add(formula.name)
    return False

class KripkeModel:
    def __init__(self):
        self.worlds = {}
        self.accessibility_relation = {}

    def add_world(self, world_name, valuation):
        self.worlds[world_name] = valuation

    def add_accessibility(self, world_from, world_to):
        if world_from not in self.accessibility_relation:
            self.accessibility_relation[world_from] = []
        self.accessibility_relation[world_from].append(world_to)

    def is_true(self, formula, world):
        if isinstance(formula, Atom):
            return formula.name in self.worlds[world]
        elif isinstance(formula, Not):
            return not self.is_true(formula.formula, world)
        elif isinstance(formula, And):
            return all(self.is_true(conj, world) for conj in formula.conjuncts)
        elif isinstance(formula, Or):
            return any(self.is_true(disj, world) for disj in formula.disjuncts)
        elif isinstance(formula, Implies):
            return not self.is_true(formula.left, world) or self.is_true(formula.right, world)
        elif isinstance(formula, Box):
            return all(self.is_true(formula.formula, w) for w in self.accessibility_relation.get(world, []))
        elif isinstance(formula, Diamond):
            return any(self.is_true(formula.formula, w) for w in self.accessibility_relation.get(world, []))
        return False

def extract_atoms(formula: Formula) -> Set[str]:
    if isinstance(formula, Atom):
        return {formula.name}
    elif isinstance(formula, Not):
        return extract_atoms(formula.formula)
    elif isinstance(formula, And):
        atoms = set()
        for conjunct in formula.conjuncts:
            atoms.update(extract_atoms(conjunct))
        return atoms
    elif isinstance(formula, Or):
        atoms = set()
        for disjunct in formula.disjuncts:
            atoms.update(extract_atoms(disjunct))
        return atoms
    elif isinstance(formula, Implies):
        return extract_atoms(formula.left).union(extract_atoms(formula.right))
    elif isinstance(formula, Box):
        return extract_atoms(formula.formula)
    elif isinstance(formula, Diamond):
        return extract_atoms(formula.formula)
    else:
        raise ValueError(f"Unknown formula type: {type(formula)}")

def build_dynamic_kripke_model(formula: Formula) -> KripkeModel:
    atoms = extract_atoms(formula)
    model = KripkeModel()

    # Create worlds based on all possible combinations of truth values for the atoms
    from itertools import product
    atom_list = list(atoms)
    num_atoms = len(atom_list)
    for i, values in enumerate(product([True, False], repeat=num_atoms)):
        world_name = f'w{i + 1}'
        valuation = {atom_list[j] for j in range(num_atoms) if values[j]}
        model.add_world(world_name, valuation)

    # Add accessibility relations (for simplicity, making it fully accessible)
    world_names = list(model.worlds.keys())
    for world_from in world_names:
        for world_to in world_names:
            model.add_accessibility(world_from, world_to)

    return model

def visualize_kripke(model: KripkeModel, formula: Formula):
    G = pydot.Dot(graph_type='digraph', rankdir='LR')

    for world in model.worlds:
        true_in_world = model.is_true(formula, world)
        color = 'green' if true_in_world else 'red'
        label = f"{world}\n({', '.join(model.worlds[world])})"
        G.add_node(pydot.Node(world, label=label, style='filled', fillcolor=color))

    for world_from, worlds_to in model.accessibility_relation.items():
        for world_to in worlds_to:
            G.add_edge(pydot.Edge(world_from, world_to))

    G.write_png('kripke_model_dynamic.png')
    print("Dynamic Kripke model visualization saved as 'kripke_model_dynamic.png'")

class Tableaux:
    def __init__(self, formula: Formula):
        self.branches: List[Branch] = [[(True, "1", formula)]]
        self.graph = pydot.Dot(graph_type='graph', rankdir='TB')
        self.node_count = 0
        self.expanded_prefixes = set()
        self.current_prefix = "1"
        self.kripke_model = KripkeModel()

    def solve(self, max_iterations=1000):
        for iteration in range(max_iterations):
            print(f"Iteration {iteration}, branches: {self.branches}")
            new_branches = self.expand()
            if new_branches == self.branches:
                break  # No more expansions possible
            self.branches = [branch for branch in new_branches if not is_closed(branch)]
            if not self.branches:
                return False  # All branches closed, formula is unsatisfiable
        return len(self.branches) > 0  # If any open branch remains, formula is satisfiable

    def add_node(self, formulas: List[Tuple[bool, str, Formula]]) -> pydot.Node:
        label = "\n".join(
            f"{prefix} {'T' if sign else 'F'} {self.formula_to_string(formula)}" for sign, prefix, formula in formulas)
        node = pydot.Node(f'node{self.node_count}', label=label, shape='box')
        self.graph.add_node(node)
        self.node_count += 1
        return node

    def add_child_nodes(self, parent_node: pydot.Node, formulas: List[Tuple[bool, str, Formula]]):
        child_node = self.add_node(formulas)
        self.graph.add_edge(pydot.Edge(parent_node, child_node))

    def expand(self):
        new_branches = []
        for branch in self.branches:
            expanded = False
            for i, (sign, prefix, formula) in enumerate(branch):
                result = apply_rule(sign, prefix, formula, self.expanded_prefixes)
                if result:
                    expanded = True
                    parent_node = self.add_node([(sign, prefix, formula)])
                    for new_branch in result:
                        new_full_branch = branch[:i] + new_branch + branch[i + 1:]
                        new_branches.append(new_full_branch)
                        self.add_child_nodes(parent_node, new_branch)
                    break
            if not expanded:
                new_branches.append(branch)
                if not self.graph.get_nodes():  # If graph is empty, add the whole branch
                    self.add_node(branch)
        return new_branches

    def save_graph(self, filename='tableau.png'):
        self.graph.write_png(filename)

    def print_tableau(self):
        for i, branch in enumerate(self.branches):
            print(f"Branch {i}:")
            for sign, prefix, formula in branch:
                print(f"  {prefix} {'T' if sign else 'F'} {self.formula_to_string(formula)}")
            print()

    @staticmethod
    def formula_to_string(formula: Formula) -> str:
        if isinstance(formula, Atom):
            return formula.name
        elif isinstance(formula, Not):
            return f"~{Tableaux.formula_to_string(formula.formula)}"
        elif isinstance(formula, And):
            return f"({' & '.join(Tableaux.formula_to_string(c) for c in formula.conjuncts)})"
        elif isinstance(formula, Or):
            return f"({' | '.join(Tableaux.formula_to_string(d) for d in formula.disjuncts)})"
        elif isinstance(formula, Implies):
            return f"({Tableaux.formula_to_string(formula.left)} -> {Tableaux.formula_to_string(formula.right)})"
        elif isinstance(formula, Box):
            return f"[]{Tableaux.formula_to_string(formula.formula)}"
        elif isinstance(formula, Diamond):
            return f"<>{Tableaux.formula_to_string(formula.formula)}"
        else:
            raise ValueError(f"Unknown formula type: {type(formula)}")

def custom_parse_formula(s: str) -> Formula:
    s = s.replace(' ', '')  # Remove all spaces
    s = s.replace('□', '[]')  # Replace □ with []
    s = s.replace('♢', '<>')  # Replace ♢ with <>

    def parse_atom(i):
        if i < len(s):
            if s[i].isalpha():
                return Atom(s[i]), i + 1
            elif s[i:i + 2] in ['[]', '<>']:
                if i + 2 < len(s):
                    if s[i + 2] == '(':
                        sub_formula, new_i = parse_parentheses(i + 2)
                        if s[i:i + 2] == '[]':
                            return Box(sub_formula), new_i
                        else:
                            return Diamond(sub_formula), new_i
                    elif s[i + 2].isalpha():
                        if s[i:i + 2] == '[]':
                            return Box(Atom(s[i + 2])), i + 3
                        else:
                            return Diamond(Atom(s[i + 2])), i + 3
        raise ValueError(f"Expected atom or modal operator at position {i}")

    def parse_not(i):
        if i < len(s) and s[i] == '~':
            sub_formula, new_i = parse_not(i + 1)
            return Not(sub_formula), new_i
        return parse_parentheses(i)

    def parse_and(i):
        left, i = parse_not(i)
        conjuncts = [left]
        while i < len(s) and s[i] == '&':
            right, i = parse_not(i + 1)
            conjuncts.append(right)
        return And(conjuncts) if len(conjuncts) > 1 else left, i

    def parse_or(i):
        left, i = parse_and(i)
        disjuncts = [left]
        while i < len(s) and s[i] == '|':
            right, i = parse_and(i + 1)
            disjuncts.append(right)
        return Or(disjuncts) if len(disjuncts) > 1 else left, i

    def parse_implies(i):
        left, i = parse_or(i)
        while i < len(s) - 1 and s[i:i + 2] == '->':
            right, i = parse_implies(i + 2)  # Recursive call for right side
            left = Implies(left, right)
        return left, i

    def parse_box(i):
        if i < len(s) - 1 and s[i:i + 2] == '[]':
            sub_formula, new_i = parse_diamond(i + 2)
            return Box(sub_formula), new_i
        return parse_implies(i)

    def parse_diamond(i):
        if i < len(s) - 1 and s[i:i + 2] == '<>':
            sub_formula, new_i = parse_diamond(i + 2)
            return Diamond(sub_formula), new_i
        return parse_box(i)

    def parse_parentheses(i):
        if i < len(s) and s[i] == '(':
            expr, i = parse_diamond(i + 1)
            if i < len(s) and s[i] == ')':
                return expr, i + 1
            raise ValueError(f"Missing closing parenthesis at position {i}")
        return parse_atom(i)

    formula, i = parse_diamond(0)
    if i < len(s):
        raise ValueError(f"Unexpected character at position {i}: '{s[i]}'")
    return formula

# ---------------------------------------------------------------------------------------------------------------------#

test_formulas = [
    # "(a|b|c)"
    # "(a&b&c)",
    # "(a->b->c)",
    # "((a&b)|(c&d))",
    # "(a->b)&(b->c)&(c->a)",
    # "[]a&<>b&c",
    # "~(a&b&c)",
    # "(a|b)->(c&d)",
    # "(a&b&c)->(d|e|f)",
    # "(a|b|c)",
    # "~(a|b)",
    # "(a->b)&(b->c)",
    # "[]a->♢b",
    # "a&b|c",
    # "(a&b)|(c&d)",
    # "~(a&b)|~(c&d)",
    "[](a->b)->[]a->[]b",  # K axiom
    # "(♢a&♢b)->♢(a&b)",  # Complex modal formula
    # "(a&~a)",  # Classic contradiction
    # "~(a|~a)",  # Negation of a tautology
    # "((a->b)&(b->c)&(c->a)&(~a&~b&~c))",  # Cyclic implications with all false
    # "~[](p & q) & ~<>(p & r) & ~<>(q & r)"
]

for formula_str in test_formulas:
    try:
        formula = custom_parse_formula(formula_str)
        print(f"Input: {formula_str}")
        print(f"Parsed: {Tableaux.formula_to_string(formula)}")
        print()

        # Tableau method
        solver = Tableaux(formula)
        result = solver.solve()
        if result:
            print(f"The formula '{Tableaux.formula_to_string(formula)}' is satisfiable.")
        else:
            print(f"The formula '{Tableaux.formula_to_string(formula)}' is unsatisfiable.")
        solver.print_tableau()
        solver.save_graph()
        print("Tableau visualization saved as 'tableau.png'")

        # Kripke model
        dynamic_model = build_dynamic_kripke_model(formula)
        visualize_kripke(dynamic_model, formula)
        print("Dynamic Kripke model visualization saved as 'kripke_model_dynamic.png'")

    except Exception as e:
        print(f"Error processing formula '{formula_str}': {str(e)}")
    print()
