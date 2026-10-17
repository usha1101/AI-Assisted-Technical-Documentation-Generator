import ast
from typing import List, Dict, Any, Optional


class CodeParser:
    """
    Parses Python source code using the native ast module.
    Extracts top-level functions, classes, and methods, including
    parameter names, type annotations, return types, and raised exceptions.
    """

    def __init__(self):
        self.last_error: Optional[Dict[str, Any]] = None

    def parse_code(self, source_code: str, raise_on_error: bool = False) -> List[Dict[str, Any]]:
        """
        Parses source code. Extracts top-level functions, classes, and class methods.
        Ignores nested/internal functions to keep documentation clean.
        
        If a SyntaxError occurs:
          - If raise_on_error is True, the SyntaxError is re-raised.
          - If raise_on_error is False, records error details in self.last_error and returns [].
        """
        self.last_error = None
        if not source_code or not source_code.strip():
            return []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            self.last_error = {
                'line': e.lineno,
                'column': e.offset,
                'message': str(e.msg) if hasattr(e, 'msg') else str(e),
                'text': e.text.strip() if e.text else None
            }
            if raise_on_error:
                raise e
            return []

        entities = []

        # Iterate over top-level module statements to avoid recursing into nested scopes
        for node in tree.body:
            # 1. Top-Level Functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entities.append(self._parse_function_node(node, source_code, entity_type='function'))

            # 2. Classes and their Methods
            elif isinstance(node, ast.ClassDef):
                entities.append(self._parse_class_node(node, source_code))

                # Extract methods defined directly in the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_entity = self._parse_function_node(
                            item,
                            source_code,
                            entity_type='method',
                            class_name=node.name
                        )
                        entities.append(method_entity)

        return entities

    def _parse_function_node(
        self,
        node: ast.AST,
        source_code: str,
        entity_type: str,
        class_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extracts structured metadata for a function or method node."""
        full_name = f"{class_name}.{node.name}" if class_name else node.name
        segment = ast.get_source_segment(source_code, node) or ""

        # Extract parameters with types and defaults
        parameters = self._extract_parameters(node.args)

        # Extract return annotation if present
        return_type = None
        if node.returns is not None:
            try:
                return_type = ast.unparse(node.returns)
            except Exception:
                return_type = None

        # Extract explicitly raised exceptions
        raises = self._extract_raised_exceptions(node)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                pass

        return {
            'name': full_name,
            'type': entity_type,
            'code': segment,
            'line_number': getattr(node, 'lineno', None),
            'end_line_number': getattr(node, 'end_lineno', None),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'parameters': parameters,
            'return_type': return_type,
            'raises': raises,
            'decorators': decorators,
            'existing_docstring': ast.get_docstring(node)
        }

    def _parse_class_node(self, node: ast.ClassDef, source_code: str) -> Dict[str, Any]:
        """Extracts structured metadata for a class definition node."""
        segment = ast.get_source_segment(source_code, node) or ""

        base_classes = []
        for base in node.bases:
            try:
                base_classes.append(ast.unparse(base))
            except Exception:
                pass

        decorators = []
        for dec in node.decorator_list:
            try:
                decorators.append(ast.unparse(dec))
            except Exception:
                pass

        method_names = [
            m.name for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        return {
            'name': node.name,
            'type': 'class',
            'code': segment,
            'line_number': getattr(node, 'lineno', None),
            'end_line_number': getattr(node, 'end_lineno', None),
            'base_classes': base_classes,
            'decorators': decorators,
            'methods': method_names,
            'existing_docstring': ast.get_docstring(node),
            'parameters': [],
            'return_type': None,
            'raises': []
        }

    def _extract_parameters(self, args_node: ast.arguments) -> List[Dict[str, Any]]:
        """Extracts names, type hints, and default values from function arguments."""
        parameters = []

        # Regular positional and keyword arguments
        num_args = len(args_node.args)
        num_defaults = len(args_node.defaults)
        default_offset = num_args - num_defaults

        for i, arg in enumerate(args_node.args):
            type_str = None
            if arg.annotation is not None:
                try:
                    type_str = ast.unparse(arg.annotation)
                except Exception:
                    pass

            default_str = None
            if i >= default_offset:
                def_idx = i - default_offset
                try:
                    default_str = ast.unparse(args_node.defaults[def_idx])
                except Exception:
                    pass

            parameters.append({
                'name': arg.arg,
                'type_annotation': type_str,
                'default_value': default_str
            })

        # *vararg (e.g. *args)
        if args_node.vararg:
            var_type = None
            if args_node.vararg.annotation is not None:
                try:
                    var_type = ast.unparse(args_node.vararg.annotation)
                except Exception:
                    pass
            parameters.append({
                'name': f"*{args_node.vararg.arg}",
                'type_annotation': var_type,
                'default_value': None
            })

        # Keyword-only arguments (e.g. *, key=val)
        for i, kwarg in enumerate(args_node.kwonlyargs):
            kw_type = None
            if kwarg.annotation is not None:
                try:
                    kw_type = ast.unparse(kwarg.annotation)
                except Exception:
                    pass

            kw_default = None
            if i < len(args_node.kw_defaults) and args_node.kw_defaults[i] is not None:
                try:
                    kw_default = ast.unparse(args_node.kw_defaults[i])
                except Exception:
                    pass

            parameters.append({
                'name': kwarg.arg,
                'type_annotation': kw_type,
                'default_value': kw_default
            })

        # **kwarg (e.g. **kwargs)
        if args_node.kwarg:
            kw_type = None
            if args_node.kwarg.annotation is not None:
                try:
                    kw_type = ast.unparse(args_node.kwarg.annotation)
                except Exception:
                    pass
            parameters.append({
                'name': f"**{args_node.kwarg.arg}",
                'type_annotation': kw_type,
                'default_value': None
            })

        return parameters

    def _extract_raised_exceptions(self, node: ast.AST) -> List[str]:
        """Extracts names of exceptions explicitly raised inside the function."""
        raises = []
        for child in ast.iter_child_nodes(node):
            # Do not descend into nested function or class definitions
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            if isinstance(child, ast.Raise):
                if child.exc is not None:
                    if isinstance(child.exc, ast.Name):
                        raises.append(child.exc.id)
                    elif isinstance(child.exc, ast.Call):
                        try:
                            raises.append(ast.unparse(child.exc.func))
                        except Exception:
                            pass
                    else:
                        try:
                            raises.append(ast.unparse(child.exc))
                        except Exception:
                            pass
            else:
                raises.extend(self._extract_raised_exceptions(child))

        # Deduplicate while preserving original order
        seen = set()
        unique_raises = []
        for r in raises:
            if r and r not in seen:
                seen.add(r)
                unique_raises.append(r)
        return unique_raises
