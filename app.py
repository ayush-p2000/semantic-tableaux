import streamlit as st
import logging
import os
from full_code import custom_parse_formula, Tableaux

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

    except Exception as e:
        logger.error(f"Error in solve_formula: {str(e)}", exc_info=True)
        return None, None, str(e), None, None, None, None


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

def main():
    st.title("Semantic Tableaux Solver")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

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

    formula_str = st.text_area("Enter the formula:", value="p & q")

    if st.button("Solve"):
        logger.debug(f"Solve button clicked with formula: {formula_str}")
        (is_valid, is_satisfiable, parsed_formula, validity_image_path, satisfiability_image_path,
         validity_accessibility_image_path, satisfiability_accessibility_image_path) = solve_formula(formula_str)

        if is_valid is not None and is_satisfiable is not None:
            st.write(f"Parsed formula: {parsed_formula}")

            st.subheader("Validity Check")
            if is_valid:
                st.success(f"The formula is valid.")
            else:
                st.error(f"The formula is not valid.")

            if validity_image_path:
                st.image(validity_image_path, caption='Validity Tableau Visualization')
                os.unlink(validity_image_path)

            if validity_accessibility_image_path:
                st.image(validity_accessibility_image_path, caption='Validity Accessibility Graph')
                os.unlink(validity_accessibility_image_path)

            st.subheader("Satisfiability Check")
            if is_satisfiable:
                st.success(f"The formula is satisfiable.")
            else:
                st.error(f"The formula is not satisfiable (contradiction).")

            if satisfiability_image_path:
                st.image(satisfiability_image_path, caption='Satisfiability Tableau Visualization')
                os.unlink(satisfiability_image_path)

            if satisfiability_accessibility_image_path:
                st.image(satisfiability_accessibility_image_path, caption='Satisfiability Accessibility Graph')
                os.unlink(satisfiability_accessibility_image_path)

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
        else:
            st.error(f"Error: {parsed_formula}")

    # Sidebar chat with AI icon and fixed input box
    st.sidebar.markdown(
        """
        <style>
        .sidebar-icon {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .sidebar-icon img {
            width: 60px;
            height: 60px;
        }
        .fixed-input {
            position: fixed;
            bottom: 20px;
            width: 100%;
            background-color: #333;
            padding: 10px;
            box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        }
        </style>
        <div class="sidebar-icon">
            <img src="https://cdn-icons-png.flaticon.com/512/4712/4712027.png" alt="AI Bot Icon">
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.title("Chat with AI")
    for message in st.session_state.chat_messages:
        with st.sidebar.chat_message(message["role"]):
            st.sidebar.markdown(message["content"])

    if prompt := st.sidebar.text_input("What is your question?", key="fixed_input", label_visibility="collapsed"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.sidebar.chat_message("user"):
            st.sidebar.markdown(prompt)
        with st.sidebar.chat_message("assistant"):
            response = process_chat_input(prompt)
            st.sidebar.markdown(response)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})

    st.sidebar.markdown(
        """
        <style>
        #fixed_input {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #0E1117;
            padding: 10px;
            z-index: 9999;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()