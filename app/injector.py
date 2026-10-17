import ast
import re
from typing import List, Dict, Any


class DocstringInjector:
    """
    Safely injects generated docstrings into Python source code directly
    beneath their corresponding function or class declarations.
    
    Processes AST nodes in reverse line order so line indices remain consistent.
    """

    @staticmethod
    def inject_docstrings(source_code: str, entities: List[Dict[str, Any]]) -> str:
        """
        Injects docstrings into source_code for matching entities.
        If an entity already has a docstring, it is replaced with the new one.
        If syntax is invalid, returns the original source_code unmodified.
        """
        if not source_code or not entities:
            return source_code

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return source_code

        lines = source_code.splitlines(keepends=True)

        # Build map of entity name -> docstring text
        doc_map = {}
        for e in entities:
            name = e.get('entity_name') or e.get('name')
            doc = e.get('generated_docstring')
            if name and doc:
                doc_map[name] = doc.strip()

        if not doc_map:
            return source_code

        # Gather targets from AST
        targets = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                targets.append((node, node.name))
            elif isinstance(node, ast.ClassDef):
                targets.append((node, node.name))
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        targets.append((item, f"{node.name}.{item.name}"))

        # Sort targets in reverse order of line number
        targets.sort(key=lambda item: item[0].lineno, reverse=True)

        for node, full_name in targets:
            docstring = doc_map.get(full_name)
            if not docstring or not node.body:
                continue

            first_stmt = node.body[0]
            stmt_line_idx = first_stmt.lineno - 1

            # Determine indentation
            if stmt_line_idx < len(lines):
                stmt_line = lines[stmt_line_idx]
                indent_match = re.match(r'^(\s*)', stmt_line)
                indent = indent_match.group(1) if (indent_match and indent_match.group(1)) else "    "
            else:
                indent = "    "

            # Check if first statement is already an existing docstring
            has_existing_doc = (
                isinstance(first_stmt, ast.Expr) and
                isinstance(first_stmt.value, ast.Constant) and
                isinstance(first_stmt.value.value, str)
            )

            # Format docstring block
            doc_lines = docstring.splitlines()
            if len(doc_lines) == 1:
                formatted_doc = f'{indent}"""{doc_lines[0]}"""\n'
            else:
                indented_body = "\n".join(
                    f"{indent}{line}" if line.strip() else ""
                    for line in doc_lines
                )
                formatted_doc = f'{indent}"""\n{indented_body}\n{indent}"""\n'

            # Check if definition header and first statement are on the same line (e.g. def f(): pass)
            if node.lineno == first_stmt.lineno and not has_existing_doc:
                raw_line = lines[stmt_line_idx]
                colon_idx = raw_line.find(":")
                if colon_idx != -1:
                    header = raw_line[:colon_idx + 1]
                    remainder = raw_line[colon_idx + 1:].strip()
                    lines[stmt_line_idx] = f"{header}\n{formatted_doc}"
                    if remainder:
                        lines.insert(stmt_line_idx + 1, f"{indent}{remainder}\n")
                    continue

            if has_existing_doc:
                start_idx = first_stmt.lineno - 1
                end_idx = getattr(first_stmt, 'end_lineno', first_stmt.lineno)
                lines[start_idx:end_idx] = [formatted_doc]
            else:
                lines.insert(stmt_line_idx, formatted_doc)

        return "".join(lines)
