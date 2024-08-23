import io
import tempfile
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict
import logging

import networkx as nx
import pydot
from matplotlib import pyplot as plt

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def run_with_timeout(func, args=(), kwargs={}, timeout_duration=10):
    result = [TimeoutError('function {} timed out after {} seconds'.format(func.__name__, timeout_duration))]

    def worker():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            result[0] = e

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout_duration)
    if thread.is_alive():
        return TimeoutError('function {} timed out after {} seconds'.format(func.__name__, timeout_duration))
    if isinstance(result[0], Exception):
        raise result[0]
    return result[0]


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


def is_satisfied(formula, pos, neg):
    if isinstance(formula, Atom):
        return formula.name in pos
    elif isinstance(formula, Not):
        return formula.formula.name in neg
    return False


def is_closed(branch: Branch, accessibility: Dict[str, Set[str]]) -> bool:
    world_formulas = defaultdict(lambda: (set(), set()))
    for sign, world, formula in branch:
        if isinstance(formula, Atom):
            if sign:
                world_formulas[world][0].add(formula.name)
            else:
                world_formulas[world][1].add(formula.name)

    for world in world_formulas:
        pos, neg = world_formulas[world]
        if pos & neg:
            return True

    return False


class Tableaux:
    def __init__(self, formula: Formula):
        self.branches = None
        self.formula = formula
        self.node_count = 0
        self.expanded_prefixes = set()
        self.current_prefix = "1"
        self.tree = {}
        self.accessibility = defaultdict(set)
        self.accessibility["1"] = set()
        self.deferred_expansions = []
        self.new_world_created = False
        self.graph = pydot.Dot(graph_type='digraph')
        self.graph.set_rankdir('TB')
        self.graph.set_size("12,16!")
        self.graph.set_margin(0.5)
        self.graph.set_graph_defaults(nodesep='0.7', ranksep='1.0')
        self.graph.set_node_defaults(shape='ellipse', style='filled', fillcolor='lightblue',
                                     width='2.5', height='1.2', fontsize='14')
        self.graph.set_edge_defaults(arrowhead='vee', arrowsize='0.9', penwidth='1.2')

    def check_validity(self, max_iterations=1000):
        # Check if the formula is valid by checking if its negation is unsatisfiable
        is_negation_satisfiable = self.check_satisfiability(max_iterations)

        if not is_negation_satisfiable:
            print("The negation is a contradiction, therefore the formula is valid.")
            return True

        # If the negation is satisfiable, the formula is not valid
        return False

    def check_satisfiability(self, max_iterations=1000):
        self.branches = [[(False, "1", self.formula)]]
        return not self.solve(max_iterations)

    def solve(self, max_iterations):
        for iteration in range(max_iterations):
            print(f"Iteration {iteration}, branches: {len(self.branches)}")
            self.new_world_created = False  # Reset the new world creation flag
            new_branches = self.expand()

            if new_branches == self.branches:
                print("No more expansions possible")
                break

            # Apply deferred expansions if no new world has been created
            if not self.new_world_created:
                self.apply_deferred_expansions()

            self.branches = new_branches

        self.build_tree()  # Build the tree after expansion is complete

        # Check if all branches are closed
        all_closed = all(is_closed(branch, self.accessibility) for branch in self.branches)
        return all_closed

    def apply_deferred_expansions(self):
        """Process the deferred expansions for T [] and F <> formulas"""
        print(f"Processing deferred expansions: {len(self.deferred_expansions)}")
        deferred_branches = []
        for branch in self.deferred_expansions:
            expanded_branches = self.expand_branch(branch)
            deferred_branches.extend(expanded_branches)

        self.branches.extend(deferred_branches)
        self.deferred_expansions.clear()  # Clear deferred expansions after processing

    def expand(self):
        new_branches = []
        for branch in self.branches:
            expanded_branches = self.expand_branch(branch)
            new_branches.extend(expanded_branches)
        return new_branches

    def expand_branch(self, branch, depth=0, parent_id=None):
        print(
            f"\nExpanding branch at depth {depth}: {[(prefix, 'T' if sign else 'F', Tableaux.formula_to_string(formula)) for sign, prefix, formula in branch]}")

        if depth > 100:  # Prevent infinite recursion
            print(f"Warning: Maximum recursion depth reached for branch: {branch}")
            return [branch]

        node_id = self.add_node(branch, parent_id)

        # First, expand all F [] formulas
        f_box_formulas = [(i, (sign, prefix, formula)) for i, (sign, prefix, formula) in enumerate(branch)
                          if isinstance(formula, Box) and not sign]

        for i, (sign, prefix, formula) in f_box_formulas:
            result = self.apply_rule(sign, prefix, formula)
            if result:
                for new_branch in result:
                    new_full_branch = branch[:i] + new_branch + branch[i + 1:]
                    expanded_branches = self.expand_branch(new_full_branch, depth + 1, node_id)
                    if expanded_branches:
                        return expanded_branches

        # Then, expand other formulas
        for i, (sign, prefix, formula) in enumerate(branch):
            if isinstance(formula, Atom):
                print(f"Atom found in branch, skipping: {Tableaux.formula_to_string(formula)}")
                continue  # Skip atomic formulas

            if isinstance(formula, Box) and sign:
                # Defer expansion of T [] formulas
                continue

            result = self.apply_rule(sign, prefix, formula)

            if result:
                print(f"Formula expanded into: {result}")
                expanded_branches = []
                for new_branch in result:
                    new_full_branch = branch[:i] + new_branch + branch[i + 1:]
                    print(
                        f"New full branch after expansion: {[(prefix, 'T' if sign else 'F', Tableaux.formula_to_string(formula)) for sign, prefix, formula in new_full_branch]}")

                    if isinstance(formula, Or) and sign:
                        for sub_branch in new_branch:
                            expanded_branches.extend(
                                self.expand_branch([sub_branch] + new_full_branch[i + 1:], depth + 1, node_id))
                    else:
                        expanded_branches.extend(self.expand_branch(new_full_branch, depth + 1, node_id))
                return expanded_branches

        # If no expansion was possible, expand deferred T [] formulas
        t_box_formulas = [(i, (sign, prefix, formula)) for i, (sign, prefix, formula) in enumerate(branch)
                          if isinstance(formula, Box) and sign]

        for i, (sign, prefix, formula) in t_box_formulas:
            result = self.apply_rule(sign, prefix, formula)
            if result:
                for new_branch in result:
                    new_full_branch = branch[:i] + new_branch + branch[i + 1:]
                    expanded_branches = self.expand_branch(new_full_branch, depth + 1, node_id)
                    if expanded_branches:
                        return expanded_branches

        # If no expansion was possible, return the branch as is
        print(
            f"No expansion possible for branch, returning as is: {[(prefix, 'T' if sign else 'F', Tableaux.formula_to_string(formula)) for sign, prefix, formula in branch]}")
        return [branch]

    def apply_rule(self, sign: bool, prefix: str, formula: Formula) -> List[List[Tuple[bool, str, Formula]]]:
        print(f"Applying rule to: {'T' if sign else 'F'} {prefix} {self.formula_to_string(formula)}")

        if isinstance(formula, Atom):
            return []  # No expansion needed for atomic formulas

        elif isinstance(formula, Not):
            return [[(not sign, prefix, formula.formula)]]

        elif isinstance(formula, And):
            if sign:
                return [[(True, prefix, conj) for conj in formula.conjuncts]]
            else:
                return [[(False, prefix, conj)] for conj in formula.conjuncts]

        elif isinstance(formula, Or):
            if sign:
                return [[(True, prefix, disj)] for disj in formula.disjuncts]
            else:
                return [[(False, prefix, disj) for disj in formula.disjuncts]]

        elif isinstance(formula, Implies):
            if sign:
                return [[(False, prefix, formula.left)], [(True, prefix, formula.right)]]
            else:
                return [[(True, prefix, formula.left), (False, prefix, formula.right)]]

        elif isinstance(formula, Box):
            if sign:
                result = []
                for accessible_world in self.accessibility[prefix]:
                    result.append((True, accessible_world, formula.formula))
                return [result] if result else []
            else:
                new_world = f"{prefix}.{len(self.accessibility[prefix]) + 1}"
                self.accessibility[prefix].add(new_world)
                self.new_world_created = True
                return [[(False, new_world, formula.formula)]]

        elif isinstance(formula, Diamond):
            if sign:
                new_world = f"{prefix}.{len(self.accessibility[prefix]) + 1}"
                self.accessibility[prefix].add(new_world)
                self.new_world_created = True
                return [[(True, new_world, formula.formula)]]
            else:
                result = []
                for accessible_world in self.accessibility[prefix]:
                    result.append((False, accessible_world, formula.formula))
                return [result] if result else []

    def print_accessibility(self):
        print("\nKripke World Relationships:")
        for world in sorted(self.accessibility.keys()):
            accessible_worlds = sorted(self.accessibility[world])
            if len(accessible_worlds) == 1 and accessible_worlds[0] == world:
                print(f"World {world}: reflexive, no other accessible worlds")
            else:
                other_worlds = [w for w in accessible_worlds if w != world]
                if world in accessible_worlds:
                    if other_worlds:
                        print(f"World {world}: reflexive, can access {', '.join(other_worlds)}")
                    else:
                        print(f"World {world}: reflexive")
                elif other_worlds:
                    print(f"World {world}: can access {', '.join(other_worlds)}")
                else:
                    print(f"World {world}: no accessible worlds")

        print("\nReflexive worlds:")
        reflexive_worlds = [world for world, accessible in self.accessibility.items() if world in accessible]
        if reflexive_worlds:
            print(", ".join(sorted(reflexive_worlds)))
        else:
            print("No reflexive worlds")

    def visualize_accessibility(self):
        """Visualizes the Kripke model accessibility relations."""
        graph = nx.DiGraph()

        # Add nodes for each world
        for world in self.accessibility:
            graph.add_node(world)

        # Add edges based on accessibility relations, excluding self-loops
        for world, accessible_worlds in self.accessibility.items():
            for accessible_world in accessible_worlds:
                if world != accessible_world:
                    graph.add_edge(world, accessible_world)

        # Choose a layout for better readability
        pos = nx.shell_layout(graph)  # You can experiment with other layouts like:
        # nx.spring_layout(graph, k=0.3, iterations=50)
        # nx.circular_layout(graph)

        # Draw the graph using matplotlib
        plt.figure(figsize=(12, 8))

        # Draw nodes with improved aesthetics
        nx.draw_networkx_nodes(graph, pos, node_size=2000, node_color='lightblue',
                               edgecolors='black', linewidths=2)
        nx.draw_networkx_labels(graph, pos, font_size=12, font_weight='bold')

        # Draw edges with improved aesthetics
        nx.draw_networkx_edges(graph, pos, edge_color='gray', arrows=True,
                               arrowsize=20, arrowstyle='->', connectionstyle='arc3,rad=0.2')

        # Add circular arrows for reflexive edges with better positioning and style
        for world in self.accessibility:
            if world in self.accessibility[world]:
                # Calculate loop position for better visibility
                loop_pos = pos[world]
                loop_pos += 0.2  # Adjust the x-coordinate for offset
                nx.draw_networkx_edges(
                    graph,
                    pos,
                    edgelist=[(world, world)],
                    connectionstyle=f"arc3, rad=0.3",  # Adjust the radius for loop size
                    arrowstyle='->',
                    arrowsize=15,
                    edge_color='gray'
                )

        plt.title("Kripke Model Accessibility", fontsize=16)
        plt.axis('off')
        # plt.tight_layout()
        plt.show()

    def build_tree(self):
        self.graph = pydot.Dot(graph_type='digraph')
        self.graph.set_rankdir('TB')
        self.graph.set_size("12,16!")
        self.graph.set_margin(0.5)

        self.graph.set_graph_defaults(nodesep='0.7', ranksep='1.0')
        self.graph.set_node_defaults(shape='ellipse', style='filled', fillcolor='lightblue',
                                     width='2.5', height='1.2', fontsize='14')
        self.graph.set_edge_defaults(arrowhead='vee', arrowsize='0.9', penwidth='1.2')

        if self.tree:
            root = next(iter(self.tree))
            self._build_tree_recursive(root)
        else:
            print("Warning: Empty tree, nothing to visualize")

    def _build_tree_recursive(self, node_id):
        node_data = self.tree[node_id]
        label = node_data['label'].replace('\n', '\\n')
        node = pydot.Node(node_id, label=label)
        if node_id == next(iter(self.tree)):
            node.set('pos', '0,0!')
        self.graph.add_node(node)
        for child_id in node_data['children']:
            child_node = self._build_tree_recursive(child_id)
            self.graph.add_edge(pydot.Edge(node, child_node))
        return node

    def add_node(self, formulas: List[Tuple[bool, str, Formula]], parent_id: str = None) -> str:
        label = "\\n".join(
            f"{prefix} {'T' if sign else 'F'} {self.formula_to_string(formula)}" for sign, prefix, formula in formulas)
        node_id = f'node{self.node_count}'
        self.tree[node_id] = {'label': label, 'children': [], 'parent': parent_id}
        self.node_count += 1
        if parent_id:
            self.tree[parent_id]['children'].append(node_id)
        return node_id

    def save_graph(self, filename='tableau.png'):
        self.graph.write_png(filename, prog='dot')

    def save_graph_to_file(self) -> str:
        logger.debug("Entering save_graph_to_file method")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                temp_filename = tmp_file.name
                logger.debug(f"Temporary file created: {temp_filename}")
                self.graph.write_png(temp_filename)
                logger.debug(f"Graph written to temporary file")
            return temp_filename
        except Exception as e:
            logger.error(f"Error in save_graph_to_file: {str(e)}")
            raise

    def print_tableau(self):
        for i, branch in enumerate(self.branches):
            print(f"Branch {i}:")
            for sign, prefix, formula in branch:
                print(f"  {prefix} {'T' if sign else 'F'} {self.formula_to_string(formula)}")
            print()

    def save_accessibility_graph(self):
        graph = nx.DiGraph()

        # Add nodes and edges
        for world in self.accessibility:
            graph.add_node(world)
            for accessible_world in self.accessibility[world]:
                graph.add_edge(world, accessible_world)

        # Create the plot
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True, node_color='lightblue',
                node_size=500, arrowsize=20, arrows=True)

        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            plt.savefig(tmp_file.name)
            plt.close()
            return tmp_file.name

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
        if i < len(s) and s[i].isalpha():
            return Atom(s[i]), i + 1
        raise ValueError(f"Expected atom at position {i}")

    def parse_not(i):
        if i < len(s) and s[i] == '~':
            sub_formula, new_i = parse_modal(i + 1)
            return Not(sub_formula), new_i
        return parse_modal(i)

    def parse_modal(i):
        if i < len(s) - 1:
            if s[i:i + 2] == '[]':
                sub_formula, new_i = parse_not(i + 2)
                return Box(sub_formula), new_i
            elif s[i:i + 2] == '<>':
                sub_formula, new_i = parse_not(i + 2)
                return Diamond(sub_formula), new_i
        return parse_parentheses(i)

    def parse_or(i):
        left, i = parse_not(i)
        while i < len(s) and s[i] == '|':
            right, i = parse_not(i + 1)
            left = Or([left, right])
        return left, i

    def parse_and(i):
        left, i = parse_or(i)
        while i < len(s) and s[i] == '&':
            right, i = parse_or(i + 1)
            left = And([left, right])
        return left, i

    def parse_implies(i):
        left, i = parse_and(i)
        if i < len(s) - 1 and s[i:i + 2] == '->':
            right, i = parse_implies(i + 2)  # Recursive call for right side
            return Implies(left, right), i
        return left, i

    def parse_parentheses(i):
        if i < len(s) and s[i] == '(':
            expr, i = parse_implies(i + 1)
            if i < len(s) and s[i] == ')':
                return expr, i + 1
            raise ValueError(f"Missing closing parenthesis at position {i}")
        return parse_atom(i)

    formula, i = parse_implies(0)
    if i < len(s):
        raise ValueError(f"Unexpected character at position {i}: '{s[i]}'")
    return formula


# Test formulas and main execution
test_formulas = [
    # "<>(p | ~p)",                  # Valid and Satisfiable
    # "[](p -> p)",                  # Valid and Satisfiable
    # "<>p -> []<>p",                # Valid in S5 modal logic
    # "[]p -> p",  # Valid (T axiom)
    # "[]p -> [][]p",                # Valid in S4 modal logic
    # "<>[]p -> []<>p",              # Valid in S5 modal logic
    # "[](<>p -> q) -> (<>[]p -> []q)",  # Valid (McKinsey's formula)
    # "<>(p & q) -> (<>p & <>q)",    # Valid and Satisfiable
    # "[]p -> <>p",                  # Not valid in general, but Satisfiable
    # "<>[]p -> []p",                # Not valid in general, but Satisfiable
    # "[](p | q) -> ([]p | []q)",    # Not valid, but Satisfiable
    # "[]p -> []<>p",                # Valid in S5
    # "<>[]p -> []p",                # Valid in S5
    # "[]<>[]p -> []p",              # Valid in S5
    # "([]p & []q) -> [](p & q)",    # Valid and Satisfiable
    # "<>(p -> q) -> ([]p -> <>q)",  # Valid and Satisfiable
    # "[]p -> (q -> []q)",           # Not valid, but Satisfiable
    # "<>(p & ~p)",                  # Not valid, Not Satisfiable (contradiction)
    # "<>p",
    # "(p | ~p)",
    # "(p & ~q)|(~p&r)",
    # "(p|q)->r",
    # "p & (p -> ~p)",
    # "(p&~q)&(q->~p)",
    # "p|~p",
    # "[](p | q) -> ([]p | <>q)"
    # "[][][][][]p"
    # "(p -> (q | z))"
    "<>(p | q) -> (<>p | <>q)"
    # "<>p -> []p"
]

for formula_str in test_formulas:
    try:
        formula = custom_parse_formula(formula_str)
        print(f"Input: {formula_str}")
        print(f"Parsed: {Tableaux.formula_to_string(formula)}")
        print()

        # Tableau method for validity
        print("Checking validity:")
        validity_solver = Tableaux(formula)
        try:
            is_valid = validity_solver.check_validity()
            print(f"Validity result: {is_valid}")
        except Exception as e:
            print(f"Error during validity check: {str(e)}")
            is_valid = None
            import traceback

            traceback.print_exc()

        print("\nValidity check tableau:")
        validity_solver.print_tableau()
        try:
            validity_solver.save_graph(filename='validity_tableau.png')
            # validity_solver.visualize_accessibility()
            print("Validity tableau visualization saved as 'validity_tableau.png'")
        except Exception as e:
            print(f"Error saving validity tableau: {str(e)}")

        print("\n" + "=" * 50 + "\n")

        # Tableau method for satisfiability
        print("Checking satisfiability:")
        satisfiability_solver = Tableaux(formula)
        try:
            is_satisfiable = satisfiability_solver.check_satisfiability()
            print(f"Satisfiability result: {is_satisfiable}")
        except Exception as e:
            print(f"Error during satisfiability check: {str(e)}")
            is_satisfiable = None
            import traceback

            traceback.print_exc()

        print("\nSatisfiability check tableau:")
        satisfiability_solver.print_tableau()
        try:
            satisfiability_solver.save_graph(filename='satisfiability_tableau.png')
            satisfiability_solver.print_accessibility()
            # satisfiability_solver.visualize_accessibility()
            print("Satisfiability tableau visualization saved as 'satisfiability_tableau.png'")
        except Exception as e:
            print(f"Error saving satisfiability tableau: {str(e)}")

        print("\n" + "=" * 50 + "\n")

        if is_valid is not None and is_satisfiable is not None:
            if is_valid:
                print(f"The formula '{Tableaux.formula_to_string(formula)}' is valid and satisfiable.")
            elif is_satisfiable:
                print(f"The formula '{Tableaux.formula_to_string(formula)}' is satisfiable but not valid.")
            else:
                print(f"The formula '{Tableaux.formula_to_string(formula)}' is not satisfiable (contradiction).")
        else:
            print("Unable to determine validity and satisfiability due to errors.")

    except Exception as e:
        print(f"Error processing formula '{formula_str}': {str(e)}")
        import traceback

        traceback.print_exc()
    print()
