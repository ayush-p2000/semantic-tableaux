import streamlit as st
import logging
import os
from coreLogic import custom_parse_formula, Tableaux

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def solve_formula(formula_str: str):
    try:
        logger.debug(f"Parsing formula: {formula_str}")
        formula = custom_parse_formula(formula_str)

        logger.debug("Creating Tableaux instance for validity check")
        validity_solver = Tableaux(formula)
        is_valid = validity_solver.check_validity()
        logger.debug(f"Validity result: {is_valid}")

        logger.debug("Saving validity graph to file")
        validity_image_path = validity_solver.save_graph_to_file()
        logger.debug(f"Validity image saved to: {validity_image_path}")

        logger.debug("Saving validity accessibility graph")
        validity_accessibility_image_path = validity_solver.save_accessibility_graph()
        logger.debug(f"Validity accessibility image saved to: {validity_accessibility_image_path}")

        logger.debug("Creating Tableaux instance for satisfiability check")
        satisfiability_solver = Tableaux(formula)
        is_satisfiable = satisfiability_solver.check_satisfiability()
        logger.debug(f"Satisfiability result: {is_satisfiable}")

        logger.debug("Saving satisfiability graph to file")
        satisfiability_image_path = satisfiability_solver.save_graph_to_file()
        logger.debug(f"Satisfiability image saved to: {satisfiability_image_path}")

        logger.debug("Saving satisfiability accessibility graph")
        satisfiability_accessibility_image_path = satisfiability_solver.save_accessibility_graph()
        logger.debug(f"Satisfiability accessibility image saved to: {satisfiability_accessibility_image_path}")

        return (is_valid, is_satisfiable, Tableaux.formula_to_string(formula),
                validity_image_path, satisfiability_image_path,
                validity_accessibility_image_path, satisfiability_accessibility_image_path)

    except ValueError as ve:
        logger.error(f"ValueError in solve_formula: {str(ve)}", exc_info=True)
        return None, None, "INVALID", None, None, None, None
    except TimeoutError as te:
        logger.error(f"TimeoutError in solve_formula: {str(te)}", exc_info=True)
        return None, None, f"Computation timed out: {str(te)}", None, None, None, None
    except Exception as e:
        logger.error(f"Unexpected error in solve_formula: {str(e)}", exc_info=True)
        return None, None, f"An unexpected error occurred: {str(e)}", None, None, None, None


def analyze_result(is_valid, is_satisfiable, formula_str):
    propositional_analysis = analyze_propositional(is_valid, is_satisfiable, formula_str)
    modal_analysis = analyze_modal(is_valid, is_satisfiable, formula_str)

    return f"""
    Propositional Logic Analysis:
    {propositional_analysis}

    Modal Logic Analysis:
    {modal_analysis}
    """


def analyze_propositional(is_valid, is_satisfiable, formula_str):
    if is_valid and is_satisfiable:
        return f"""
        In propositional logic, the formula '{formula_str}' is a tautology:
        - It is true under all possible truth assignments to its atomic propositions.
        - Its truth table would show 'True' for all rows.
        - It can be derived from axioms using rules of inference.
        - Its negation is unsatisfiable (a contradiction).
        """
    elif not is_valid and is_satisfiable:
        return f"""
        In propositional logic, the formula '{formula_str}' is contingent:
        - Its truth value depends on the truth assignments of its atomic propositions.
        - Its truth table would show both 'True' and 'False' entries.
        - It's neither a tautology nor a contradiction.
        - Both this formula and its negation are satisfiable.
        """
    elif not is_valid and not is_satisfiable:
        return f"""
        In propositional logic, the formula '{formula_str}' is a contradiction:
        - It is false under all possible truth assignments to its atomic propositions.
        - Its truth table would show 'False' for all rows.
        - It's logically equivalent to 'p ∧ ¬p' for any proposition p.
        - Its negation is a tautology.
        """
    else:
        return "Error: Invalid result combination in propositional logic."


def analyze_modal(is_valid, is_satisfiable, formula_str):
    if is_valid and is_satisfiable:
        return f"""
        In modal logic, the formula '{formula_str}' is valid (necessarily true):
        - It is true in all possible worlds of all Kripke models.
        - It represents a necessary truth in the modal system.
        - It's analogous to a tautology in propositional logic, but across possible worlds.
        - Examples include axioms of the modal system (e.g., □(p → q) → (□p → □q) in K).
        """
    elif not is_valid and is_satisfiable:
        return f"""
        In modal logic, the formula '{formula_str}' is satisfiable but not valid:
        - There exists at least one Kripke model with a world where the formula is true.
        - However, it's not true in all worlds of all models.
        - It represents a contingent statement in modal logic.
        - Its truth value may vary across different possible worlds or different Kripke models.
        - It could be:
          1. Possibly true but not necessary (true in some but not all worlds).
          2. True in the actual world but not in all possible worlds.
        - The specific modal operators (□, ◇) in the formula affect its interpretation across worlds.
        """
    elif not is_valid and not is_satisfiable:
        return f"""
        In modal logic, the formula '{formula_str}' is unsatisfiable (necessarily false):
        - It is false in all possible worlds of all Kripke models.
        - It represents an impossible statement in the modal system.
        - It's analogous to a contradiction in propositional logic, but across possible worlds.
        - Its negation is valid (necessarily true) in the modal system.
        - Examples include formulas like '□p ∧ ◇¬p' (necessarily p and possibly not p).
        """
    else:
        return "Error: Invalid result combination in modal logic."


def process_chat_input(prompt):
    if "solve" in prompt.lower():
        return "To solve a formula, enter it in the main text area and click the 'Solve' button."
    elif "syntax" in prompt.lower():
        return """
        Syntax:
        - Atoms: lowercase letters (e.g., p, q, r)
        - Negation: ~ (e.g., ~p)
        - Conjunction: & (e.g., p & q)
        - Disjunction: | (e.g., p | q)
        - Implication: -> (e.g., p -> q)
        - Box (Necessity): [] (e.g., []p)
        - Diamond (Possibility): <> (e.g., <>p)
        """
    else:
        return (f"I'm an AI assistant for the Semantic Tableaux Solver. You asked: '{prompt}'. How can I help you with "
                f"modal logic formulas?")


def analyze_formula_structure(formula_str):
    modal_operators = ['□', '◇', '[]', '<>']
    has_modal = any(op in formula_str for op in modal_operators)

    analysis = f"The formula '{formula_str}' is a "
    if has_modal:
        analysis += "modal logic formula. "
        if '□' in formula_str or '[]' in formula_str:
            analysis += "It contains the necessity operator (□ or []), which means 'it is necessary that' or 'in all accessible worlds'. "
        if '◇' in formula_str or '<>' in formula_str:
            analysis += "It contains the possibility operator (◇ or <>), which means 'it is possible that' or 'in at least one accessible world'. "
    else:
        analysis += "propositional logic formula. "

    if '->' in formula_str:
        analysis += "It involves implication, which might be analyzing conditional statements. "
    if '&' in formula_str:
        analysis += "It uses conjunction, combining multiple conditions. "
    if '|' in formula_str:
        analysis += "It includes disjunction, representing alternative conditions. "
    if '~' in formula_str:
        analysis += "It employs negation, which might be crucial for its logical properties. "

    return analysis


def display_solution(solution):
    formula_str, is_valid, is_satisfiable, parsed_formula, validity_image_path, satisfiability_image_path, \
        validity_accessibility_image_path, satisfiability_accessibility_image_path = solution

    st.write(f"Parsed formula: {parsed_formula}")

    st.subheader("Validity Check")
    if is_valid:
        st.success(f"The formula is valid.")
    else:
        st.error(f"The formula is not valid.")

    if validity_image_path:
        st.image(validity_image_path, caption='Validity Tableau Visualization')

    if validity_accessibility_image_path:
        st.image(validity_accessibility_image_path, caption='Validity Accessibility Graph')

    st.subheader("Satisfiability Check")
    if is_satisfiable:
        st.success(f"The formula is satisfiable.")
    else:
        st.error(f"The formula is not satisfiable (contradiction).")

    if satisfiability_image_path:
        st.image(satisfiability_image_path, caption='Satisfiability Tableau Visualization')

    if satisfiability_accessibility_image_path:
        st.image(satisfiability_accessibility_image_path, caption='Satisfiability Accessibility Graph')

    st.subheader("Conclusion")
    if is_valid and is_satisfiable:
        st.write("The formula is valid and satisfiable.")
    elif is_satisfiable:
        st.write("The formula is satisfiable but not valid.")
    else:
        st.write("The formula is not satisfiable (contradiction).")

    st.subheader("Analysis")
    analysis = analyze_result(is_valid, is_satisfiable, parsed_formula)
    st.markdown(analysis)

    st.subheader("Formula Structure Analysis")
    structure_analysis = analyze_formula_structure(parsed_formula)
    st.write(structure_analysis)


def select_solution(index):
    st.session_state.selected_index = index
    st.session_state.current_formula = st.session_state.solutions[index][0]
    st.session_state.editing = True


def main():
    st.title("Semantic Tableaux Solver")

    if "solutions" not in st.session_state:
        st.session_state.solutions = []

    if "current_formula" not in st.session_state:
        st.session_state.current_formula = "p & q"

    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None

    if "editing" not in st.session_state:
        st.session_state.editing = False

    # Sidebar
    st.sidebar.title("Solution History")
    solutions_to_remove = []
    for i, solution in enumerate(st.session_state.solutions):
        col1, col2 = st.sidebar.columns([5, 1])
        with col1:
            if st.button(f"Solution {i + 1}: {solution[0]}", key=f"solution_{i}", use_container_width=True,
                         on_click=select_solution, args=(i,)):
                pass
        with col2:
            if st.button("🗑️", key=f"delete_{i}", help="Delete this solution"):
                solutions_to_remove.append(i)

    # Remove deleted solutions
    if solutions_to_remove:
        for index in reversed(solutions_to_remove):
            if 0 <= index < len(st.session_state.solutions):
                del st.session_state.solutions[index]
                if st.session_state.selected_index is not None:
                    if index < st.session_state.selected_index:
                        st.session_state.selected_index -= 1
                    elif index == st.session_state.selected_index:
                        st.session_state.selected_index = None
                        st.session_state.current_formula = "p & q"
                        st.session_state.editing = False
        if st.session_state.solutions:
            if st.session_state.selected_index is None or st.session_state.selected_index >= len(
                    st.session_state.solutions):
                st.session_state.selected_index = len(st.session_state.solutions) - 1
                st.session_state.current_formula = st.session_state.solutions[st.session_state.selected_index][0]
                st.session_state.editing = True
        else:
            st.session_state.selected_index = None
            st.session_state.current_formula = "p & q"
            st.session_state.editing = False
        st.rerun()

    # Main content
    st.write("""
    This app uses the tableau method to check the validity and satisfiability of modal logic formulas.

    Syntax:
    - Atoms: lowercase letters (e.g., p, q, r)
    - Negation: ~ (e.g., ~p)
    - Conjunction: & (e.g., p & q)
    - Disjunction: | (e.g., p | q)
    - Implication: -> (e.g., p -> q)
    - Box (Necessity): [] (e.g., []p)
    - Diamond (Possibility): <> (e.g., <>p)

    You can use parentheses to group expressions.
    """)

    formula_str = st.text_input("Enter the formula:", value=st.session_state.current_formula, key="formula_input")

    if formula_str != st.session_state.current_formula:
        st.session_state.current_formula = formula_str
        if not st.session_state.editing:
            st.session_state.selected_index = None

    if st.button("Solve"):
        logger.debug(f"Solve button clicked with formula: {formula_str}")
        (is_valid, is_satisfiable, parsed_formula, validity_image_path, satisfiability_image_path,
         validity_accessibility_image_path, satisfiability_accessibility_image_path) = solve_formula(formula_str)

        if is_valid is not None and is_satisfiable is not None:
            solution = (formula_str, is_valid, is_satisfiable, parsed_formula, validity_image_path,
                        satisfiability_image_path, validity_accessibility_image_path,
                        satisfiability_accessibility_image_path)

            if st.session_state.editing and st.session_state.selected_index is not None:
                # Update existing solution
                st.session_state.solutions[st.session_state.selected_index] = solution
            else:
                # Add new solution
                st.session_state.solutions.append(solution)
                st.session_state.selected_index = len(st.session_state.solutions) - 1

            st.session_state.current_formula = formula_str
            st.session_state.editing = False
            st.rerun()
        else:
            if parsed_formula == "INVALID":
                st.error("Invalid formula. Please check your input and try again.")
            else:
                st.error(parsed_formula)  # Display other error messages
            logger.error(f"Error solving formula: {parsed_formula}")
    if st.session_state.selected_index is not None:
        display_solution(st.session_state.solutions[st.session_state.selected_index])


if __name__ == "__main__":
    main()