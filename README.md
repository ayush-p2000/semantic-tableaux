# Semantic Tableaux Solver

## Overview

The Semantic Tableaux Solver is a web application that uses the tableau method to check the validity and satisfiability of modal logic formulas. It provides a user-friendly interface for inputting formulas, visualizing tableau trees, and analyzing the results in both propositional and modal logic contexts.

## Features

- Parse and validate modal logic formulas
- Check formula validity and satisfiability
- Visualize tableau trees for both validity and satisfiability checks
- Display Kripke model accessibility graphs
- Provide detailed analysis of formula properties
- Store and manage solution history

## Github Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/semantic-tableaux-solver.git
   cd semantic-tableaux-solver
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
   
## Manual Installation

1. Unzip the downloaded zip file.
####
2. Open the folder in your IDE (PyCharm, VSCode, etc.)
####
3. Open Terminal in the path of your project folder and type down the commands below. 
####
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## User Manual

### Entering Formulas

Use the following syntax to enter modal logic formulas:

- Atoms: lowercase letters (e.g., p, q, r)
- Negation: ~ (e.g., ~p)
- Conjunction: & (e.g., p & q)
- Disjunction: | (e.g., p | q)
- Implication: -> (e.g., p -> q)
- Box (Necessity): [] or □ (e.g., []p or □p)
- Diamond (Possibility): <> or ◇ (e.g., <>p or ◇p)

You can use parentheses to group expressions.

### Solving Formulas

1. Enter your formula in the text input field.
2. Click the "Solve" button to process the formula.
3. The app will display the results, including:
   - Validity check
   - Satisfiability check
   - Tableau visualizations
   - Kripke model accessibility graphs
   - Detailed analysis of the formula's properties

### Interpreting Results

- **Valid**: The formula is true in all possible worlds of all Kripke models.
- **Satisfiable**: There exists at least one Kripke model with a world where the formula is true.
- **Unsatisfiable**: The formula is false in all possible worlds of all Kripke models.

### Managing Solutions

- The sidebar displays a history of solved formulas.
- Click on a previous solution to view its details again.
- Use the delete button (🗑️) to remove a solution from the history.

### Analyzing Formula Structure

The app provides an analysis of the formula's structure, including:
- Whether it's a modal or propositional logic formula
- The presence and meaning of modal operators
- The use of logical connectives (implication, conjunction, disjunction, negation)

## Troubleshooting

- If you encounter an "Invalid formula" error, check your syntax and ensure all parentheses are properly balanced.
- For complex formulas that take too long to process, try simplifying the formula or breaking it down into smaller parts.

## Contributing

Contributions to the Semantic Tableaux Solver are welcome! Please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.