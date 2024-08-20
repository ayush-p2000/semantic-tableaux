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

        logger.debug("Creating Tableaux instance for satisfiability check")
        satisfiability_solver = Tableaux(formula)
        is_satisfiable = satisfiability_solver.check_satisfiability()
        logger.debug(f"Satisfiability result: {is_satisfiable}")

        logger.debug("Saving satisfiability graph to file")
        satisfiability_image_path = satisfiability_solver.save_graph_to_file()
        logger.debug(f"Satisfiability image saved to: {satisfiability_image_path}")

        return is_valid, is_satisfiable, Tableaux.formula_to_string(
            formula), validity_image_path, satisfiability_image_path

    except Exception as e:
        logger.error(f"Error in solve_formula: {str(e)}", exc_info=True)
        return None, None, str(e), None, None


def analyze_result(is_valid, is_satisfiable, formula_str):
    if is_valid and is_satisfiable:
        analysis = f"""
        The formula '{formula_str}' is both valid and satisfiable. This means:
        1. Validity: The formula is true under all possible interpretations in all possible worlds. 
           It's a tautology in modal logic.
        2. Satisfiability: There exists at least one interpretation in which the formula is true. 
           This is always the case for valid formulas.
        In modal logic, this indicates a necessary truth that holds across all possible worlds.
        """
    elif not is_valid and is_satisfiable:
        analysis = f"""
        The formula '{formula_str}' is satisfiable but not valid. This means:
        1. Not Valid: There exists at least one interpretation or possible world where the formula is false. 
           It's not a tautology.
        2. Satisfiable: There exists at least one interpretation or possible world where the formula is true.
        This is the most common case for modal logic formulas. It indicates a contingent truth - 
        something that is possible but not necessary. The formula holds in some possible worlds but not in others.
        """
    elif not is_valid and not is_satisfiable:
        analysis = f"""
        The formula '{formula_str}' is neither valid nor satisfiable. This means:
        1. Not Valid: It's false in at least one possible world (actually, in all possible worlds).
        2. Not Satisfiable: There is no interpretation or possible world where the formula is true. 
           This makes it a contradiction in modal logic.
        This indicates an impossibility or a necessarily false statement in modal logic.
        """
    else:
        analysis = "Error: Invalid result combination. A formula cannot be valid and unsatisfiable."
    return analysis


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
        is_valid, is_satisfiable, parsed_formula, validity_image_path, satisfiability_image_path = solve_formula(
            formula_str)

        if is_valid is not None and is_satisfiable is not None:
            st.write(f"Parsed formula: {parsed_formula}")

            st.subheader("Validity Check")
            st.write("Valid" if is_valid else "Not Valid")
            if validity_image_path:
                st.image(validity_image_path, caption='Validity Tableau Visualization')
                os.unlink(validity_image_path)

            st.subheader("Satisfiability Check")
            st.write("Satisfiable" if is_satisfiable else "Not Satisfiable (Contradiction)")
            if satisfiability_image_path:
                st.image(satisfiability_image_path, caption='Satisfiability Tableau Visualization')
                os.unlink(satisfiability_image_path)

            st.subheader("Conclusion")
            if is_valid and is_satisfiable:
                st.write("The formula is valid and satisfiable.")
            elif is_satisfiable:
                st.write("The formula is satisfiable but not valid.")
            else:
                st.write("The formula is not satisfiable (contradiction).")

            st.subheader("Analysis")
            analysis = analyze_result(is_valid, is_satisfiable, parsed_formula)
            st.write(analysis)
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