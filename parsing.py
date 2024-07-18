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


def main():
    # Example usage:
    input_formula = "((p -> q) & ((~q -> ~p) & (~(p <-> q))))"
    parsed_formula = parse_formula(input_formula)
    print(parsed_formula)


if __name__ == '__main__':
    main()
