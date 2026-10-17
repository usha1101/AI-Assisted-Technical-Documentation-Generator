import unittest
from app.models import DocstringStyle
from app.formatter import DocstringFormatter


class TestDocstringFormatter(unittest.TestCase):
    def setUp(self):
        self.summary = "Calculate the total cost."
        self.params = [
            {"name": "price", "type_annotation": "float", "default_value": None},
            {"name": "discount", "type_annotation": "float", "default_value": "0.1"},
            {"name": "self", "type_annotation": None, "default_value": None}  # Should be omitted
        ]
        self.return_type = "float"
        self.raises = ["ValueError"]

    def test_concise_style(self):
        doc = DocstringFormatter.format_docstring(
            summary=self.summary,
            parameters=self.params,
            return_type=self.return_type,
            raises=self.raises,
            style=DocstringStyle.CONCISE
        )
        self.assertEqual(doc, self.summary)

    def test_google_style(self):
        doc = DocstringFormatter.format_docstring(
            summary=self.summary,
            parameters=self.params,
            return_type=self.return_type,
            raises=self.raises,
            style=DocstringStyle.GOOGLE
        )
        self.assertIn("Args:", doc)
        self.assertIn("price (float):", doc)
        self.assertIn("discount (float): The discount argument. Defaults to 0.1.", doc)
        self.assertNotIn("self", doc)
        self.assertIn("Returns:\n    float: The computed result.", doc)
        self.assertIn("Raises:\n    ValueError:", doc)

    def test_sphinx_style(self):
        doc = DocstringFormatter.format_docstring(
            summary=self.summary,
            parameters=self.params,
            return_type=self.return_type,
            raises=self.raises,
            style=DocstringStyle.SPHINX
        )
        self.assertIn(":param price: The price argument.", doc)
        self.assertIn(":type price: float", doc)
        self.assertIn(":param discount: The discount argument. Defaults to 0.1.", doc)
        self.assertIn(":return: The computed result.", doc)
        self.assertIn(":rtype: float", doc)
        self.assertIn(":raises ValueError:", doc)

    def test_numpy_style(self):
        doc = DocstringFormatter.format_docstring(
            summary=self.summary,
            parameters=self.params,
            return_type=self.return_type,
            raises=self.raises,
            style=DocstringStyle.NUMPY
        )
        self.assertIn("Parameters\n----------", doc)
        self.assertIn("price : float", doc)
        self.assertIn("discount : float, optional", doc)
        self.assertIn("Returns\n-------", doc)
        self.assertIn("Raises\n------", doc)


if __name__ == '__main__':
    unittest.main()
