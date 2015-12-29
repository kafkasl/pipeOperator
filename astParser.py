import ast
import operator as op


class OperationParser:

    def __init__(self):
    # supported self.operators
        self.operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                          ast.Div: op.truediv, ast.Pow: op.pow}

    def get_result(self, expression):
        """
        >>> self._evalexpr('2^6')
        4
        >>> self._evalexpr('2**6')
        64
        >>> self._evalexpr('1 + 2*3**(4^5) / (6 + -7)')
        -5.0
        """
        return self._eval(ast.parse(expression, mode='eval').body)

    def _eval(self, node):

        if isinstance(node, ast.Num):  # <number>
            return node.n

        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            operation = self.operators[type(node.op)]
            return operation(self._eval(node.left), self._eval(node.right))

        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            operation = self.operators[type(node.op)]
            return self.operators[type(node.op)](self._eval(node.operand))

        else:
            raise TypeError(node)
