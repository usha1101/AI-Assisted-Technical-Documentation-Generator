import unittest
from app.parser import CodeParser


class TestCodeParser(unittest.TestCase):
    def setUp(self):
        self.parser = CodeParser()

    def test_parse_simple_function(self):
        code = """
def add(a: int, b: int = 0) -> int:
    \"\"\"Existing docstring.\"\"\"
    return a + b
"""
        entities = self.parser.parse_code(code)
        self.assertEqual(len(entities), 1)
        entity = entities[0]
        self.assertEqual(entity['name'], 'add')
        self.assertEqual(entity['type'], 'function')
        self.assertEqual(entity['return_type'], 'int')
        self.assertEqual(entity['existing_docstring'], 'Existing docstring.')
        self.assertFalse(entity['is_async'])
        self.assertEqual(len(entity['parameters']), 2)
        self.assertEqual(entity['parameters'][0]['name'], 'a')
        self.assertEqual(entity['parameters'][0]['type_annotation'], 'int')
        self.assertIsNone(entity['parameters'][0]['default_value'])
        self.assertEqual(entity['parameters'][1]['name'], 'b')
        self.assertEqual(entity['parameters'][1]['type_annotation'], 'int')
        self.assertEqual(entity['parameters'][1]['default_value'], '0')

    def test_parse_class_and_methods(self):
        code = """
class Calculator:
    \"\"\"Calculator class.\"\"\"
    def __init__(self, precision: int = 2):
        self.precision = precision

    def compute(self, x: float) -> float:
        if x < 0:
            raise ValueError("Must be positive")
        return round(x, self.precision)
"""
        entities = self.parser.parse_code(code)
        # Should have Calculator (class), Calculator.__init__ (method), Calculator.compute (method)
        self.assertEqual(len(entities), 3)

        cls_entity = entities[0]
        self.assertEqual(cls_entity['name'], 'Calculator')
        self.assertEqual(cls_entity['type'], 'class')
        self.assertEqual(cls_entity['methods'], ['__init__', 'compute'])

        init_method = entities[1]
        self.assertEqual(init_method['name'], 'Calculator.__init__')
        self.assertEqual(init_method['type'], 'method')

        compute_method = entities[2]
        self.assertEqual(compute_method['name'], 'Calculator.compute')
        self.assertEqual(compute_method['type'], 'method')
        self.assertEqual(compute_method['return_type'], 'float')
        self.assertIn('ValueError', compute_method['raises'])

    def test_nested_functions_are_ignored(self):
        code = """
def outer_func(x):
    def inner_helper(y):
        return y * 2
    return inner_helper(x)
"""
        entities = self.parser.parse_code(code)
        self.assertEqual(len(entities), 1)
        self.assertEqual(entities[0]['name'], 'outer_func')

    def test_async_functions(self):
        code = """
async def fetch_data(url: str) -> dict:
    return {"url": url}
"""
        entities = self.parser.parse_code(code)
        self.assertEqual(len(entities), 1)
        self.assertTrue(entities[0]['is_async'])

    def test_decorators_captured(self):
        code = """
@timer_decorator
@custom_tag("analytics")
def process():
    pass
"""
        entities = self.parser.parse_code(code)
        self.assertEqual(len(entities), 1)
        self.assertEqual(len(entities[0]['decorators']), 2)
        self.assertIn('timer_decorator', entities[0]['decorators'][0])

    def test_syntax_error_handling(self):
        invalid_code = "def broken_func(:\n    pass"
        entities = self.parser.parse_code(invalid_code, raise_on_error=False)
        self.assertEqual(entities, [])
        self.assertIsNotNone(self.parser.last_error)
        self.assertEqual(self.parser.last_error['line'], 1)

        with self.assertRaises(SyntaxError):
            self.parser.parse_code(invalid_code, raise_on_error=True)

    def test_empty_input(self):
        self.assertEqual(self.parser.parse_code(""), [])
        self.assertEqual(self.parser.parse_code("   \n\t  "), [])


if __name__ == '__main__':
    unittest.main()
