import ast

class CodeParser:
    def parse_code(self, source_code: str):
        """
        Parses source code. Extracts ONLY top-level functions, classes, 
        and methods inside classes. Ignores nested/internal functions.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return []

        entities = []
        
        # We manually iterate over the top-level nodes of the module
        # instead of using ast.walk() which goes deep recursively immediately.
        for node in tree.body:
            # 1. Top-Level Functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                segment = ast.get_source_segment(source_code, node)
                entities.append({
                    'type': 'function',
                    'name': node.name,
                    'code': segment
                })
            
            # 2. Classes and their Methods
            elif isinstance(node, ast.ClassDef):
                class_segment = ast.get_source_segment(source_code, node)
                entities.append({
                    'type': 'class',
                    'name': node.name,
                    'code': class_segment
                })
                
                # Check methods inside the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_segment = ast.get_source_segment(source_code, item)
                        # We identify methods by className.methodName
                        entities.append({
                            'type': 'method',
                            'name': f"{node.name}.{item.name}",
                            'code': method_segment
                        })
        
        return entities
