import unittest
from coreLogic import custom_parse_formula, Tableaux


class TestKModalLogicTableauxSolver(unittest.TestCase):

    def test_valid_in_K(self):
        valid_formulas = [
            "(p | ~p)",  # Propositional tautology
            "[](p -> q) -> ([]p -> []q)",  # K axiom
        ]
        for formula in valid_formulas:
            with self.subTest(formula=formula):
                parsed_formula = custom_parse_formula(formula)
                solver = Tableaux(parsed_formula)
                self.assertTrue(solver.check_validity(), f"Formula should be valid in K: {formula}")
                self.assertTrue(solver.check_satisfiability(), f"Formula should be satisfiable: {formula}")

    def test_satisfiable_but_not_valid_in_K(self):
        satisfiable_formulas = [
            "<>(p | ~p)",
            "[]p -> p",  # T axiom, satisfiable but not valid in K
            "p -> <>p",  # Dual of T axiom, satisfiable but not valid in K
            "[]p -> <>p",
            "<>[]p -> []p",
            "[](p | q) -> ([]p | []q)",
            "[]p -> (q -> []q)",
            "<>p",
            "[]p",
            "[]p -> [][]p",  # 4 axiom, satisfiable but not valid in K
            "<>[]p -> p",  # B axiom, satisfiable but not valid in K
        ]
        for formula in satisfiable_formulas:
            with self.subTest(formula=formula):
                parsed_formula = custom_parse_formula(formula)
                solver = Tableaux(parsed_formula)
                self.assertFalse(solver.check_validity(), f"Formula should not be valid in K: {formula}")
                self.assertTrue(solver.check_satisfiability(), f"Formula should be satisfiable: {formula}")

    def test_unsatisfiable_formulas(self):
        unsatisfiable_formulas = [
            "p & ~p",
            "[](p & ~p)",
            "<>(p & ~p)",
            "(p & ~q) & (q & ~p)",
        ]
        for formula in unsatisfiable_formulas:
            with self.subTest(formula=formula):
                parsed_formula = custom_parse_formula(formula)
                solver = Tableaux(parsed_formula)
                self.assertFalse(solver.check_validity(), f"Formula should not be valid: {formula}")
                self.assertFalse(solver.check_satisfiability(), f"Formula should not be satisfiable: {formula}")

    def test_complex_formulas_in_K(self):
        complex_formulas = [
            "[]p -> [](p | q)",
            "<>(p & q) -> (<>p & <>q)",
            "[](p -> q) -> (<>p -> <>q)",
            "([]p & []q) -> [](p | q)",
            "<>(p -> q) -> ([]p -> <>q)",
        ]
        for formula in complex_formulas:
            with self.subTest(formula=formula):
                parsed_formula = custom_parse_formula(formula)
                solver = Tableaux(parsed_formula)
                is_valid = solver.check_validity()
                is_satisfiable = solver.check_satisfiability()
                self.assertIsNotNone(is_valid, f"Validity check should not fail for: {formula}")
                self.assertIsNotNone(is_satisfiable, f"Satisfiability check should not fail for: {formula}")
                if is_valid:
                    self.assertTrue(is_satisfiable, f"Valid formula should also be satisfiable: {formula}")

    def test_nested_modalities_in_K(self):
        nested_formulas = [
            "[]<>[]p -> <>[](p | q)",
            "[]<>(p & q) -> (<>[]p & <>[]q)",
            "[](p -> q) -> ([]p -> []q)",
            "<>[]<>[]p -> []<>[]<>p",
        ]
        for formula in nested_formulas:
            with self.subTest(formula=formula):
                parsed_formula = custom_parse_formula(formula)
                solver = Tableaux(parsed_formula)
                is_valid = solver.check_validity()
                is_satisfiable = solver.check_satisfiability()
                self.assertIsNotNone(is_valid, f"Validity check should not fail for: {formula}")
                self.assertIsNotNone(is_satisfiable, f"Satisfiability check should not fail for: {formula}")
                if is_valid:
                    self.assertTrue(is_satisfiable, f"Valid formula should also be satisfiable: {formula}")


if __name__ == '__main__':
    unittest.main()
