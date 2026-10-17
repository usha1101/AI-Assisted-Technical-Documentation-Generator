import ast
import unittest
from app.injector import DocstringInjector


class TestDocstringInjector(unittest.TestCase):
    def test_inject_simple_function(self):
        source = """def add(a, b):
    return a + b
"""
        entities = [{
            "entity_name": "add",
            "generated_docstring": "Add two numbers."
        }]
        result = DocstringInjector.inject_docstrings(source, entities)
        # Verify valid Python syntax
        tree = ast.parse(result)
        self.assertEqual(ast.get_docstring(tree.body[0]), "Add two numbers.")

    def test_inject_class_and_method(self):
        source = """class MathTool:
    def multiply(self, x, y):
        return x * y
"""
        entities = [
            {"entity_name": "MathTool", "generated_docstring": "A mathematical utility class."},
            {"entity_name": "MathTool.multiply", "generated_docstring": "Multiply two numbers."}
        ]
        result = DocstringInjector.inject_docstrings(source, entities)
        tree = ast.parse(result)
        cls_node = tree.body[0]
        self.assertEqual(ast.get_docstring(cls_node), "A mathematical utility class.")
        method_node = cls_node.body[1]
        self.assertEqual(ast.get_docstring(method_node), "Multiply two numbers.")

    def test_replace_existing_docstring(self):
        source = """def greet(name):
    \"\"\"Old docstring.\"\"\"
    return f"Hello, {name}"
"""
        entities = [{
            "entity_name": "greet",
            "generated_docstring": "New improved docstring."
        }]
        result = DocstringInjector.inject_docstrings(source, entities)
        tree = ast.parse(result)
        self.assertEqual(ast.get_docstring(tree.body[0]), "New improved docstring.")

    def test_multiline_docstring_indentation(self):
        source = """def divide(a, b):
    return a / b
"""
        docstring = """Divide a by b.

Args:
    a (float): Dividend.
    b (float): Divisor."""

        entities = [{
            "entity_name": "divide",
            "generated_docstring": docstring
        }]
        result = DocstringInjector.inject_docstrings(source, entities)
        tree = ast.parse(result)
        self.assertEqual(ast.get_docstring(tree.body[0]).strip(), docstring.strip())


if __name__ == '__main__':
    unittest.main()
