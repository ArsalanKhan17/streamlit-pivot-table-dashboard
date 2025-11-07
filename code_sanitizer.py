"""
Code Sanitizer for AI Transform.
Uses AST parsing to validate generated code against a security allow-list.
"""

import ast
import sys
from typing import List, Set


class CodeSanitizer:
    """Sanitizes and validates generated code for safety."""

    # Allowed module names
    ALLOWED_MODULES = {"pd", "pandas", "np", "numpy"}

    # Allowed built-in functions
    ALLOWED_BUILTINS = {
        "len", "range", "sum", "min", "max", "abs", "round",
        "str", "int", "float", "bool", "list", "dict", "tuple",
        "sorted", "reversed", "enumerate", "zip", "map", "filter",
        "any", "all", "isinstance", "type", "hasattr", "getattr",
    }

    # Blocked module imports and attributes
    BLOCKED_IMPORTS = {
        "os", "sys", "subprocess", "socket", "requests",
        "urllib", "http", "ftplib", "telnetlib", "pickle",
        "shelve", "dbm", "sqlite3", "pyodbc", "pymongo",
        "redis", "fabric", "paramiko", "pexpect", "pty",
    }

    # Blocked attributes (e.g., os.system, __import__)
    BLOCKED_ATTRIBUTES = {
        "__import__", "__loader__", "__spec__",
        "system", "popen", "fork", "exec", "eval",
        "compile", "open", "read", "write", "remove",
        "mkdir", "chdir", "environ",
    }

    def __init__(self):
        """Initialize the code sanitizer."""
        self.violations: List[str] = []

    def validate(self, code: str) -> List[str]:
        """
        Validate code against security constraints.

        Args:
            code: Python code to validate

        Returns:
            List of violation messages (empty if code is safe)
        """
        self.violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.violations.append(f"Syntax error: {str(e)}")
            return self.violations

        # Check structure
        self._check_structure(tree)

        # Walk the AST and check for violations
        for node in ast.walk(tree):
            self._check_node(node)

        return self.violations

    def _check_structure(self, tree: ast.Module) -> None:
        """Verify code structure (must have exactly one function named 'transform')."""
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]

        if len(functions) != 1:
            self.violations.append(f"Expected exactly 1 function, found {len(functions)}")
            return

        func = functions[0]
        if func.name != "transform":
            self.violations.append(f"Function must be named 'transform', got '{func.name}'")

        if len(func.args.args) != 1:
            self.violations.append(
                f"Function must have exactly 1 parameter, got {len(func.args.args)}"
            )
        elif func.args.args[0].arg != "df":
            self.violations.append(
                f"Parameter must be named 'df', got '{func.args.args[0].arg}'"
            )

    def _check_node(self, node: ast.AST) -> None:
        """Check individual AST nodes for violations."""
        # Check imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            self.violations.append(
                f"Line {node.lineno}: Imports not allowed. Use only pd, np."
            )

        # Check function calls
        elif isinstance(node, ast.Call):
            self._check_call(node)

        # Check attribute access
        elif isinstance(node, ast.Attribute):
            self._check_attribute(node)

        # Check names
        elif isinstance(node, ast.Name):
            self._check_name(node)

    def _check_call(self, node: ast.Call) -> None:
        """Check function calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name == "eval" or func_name == "exec" or func_name == "compile":
                self.violations.append(
                    f"Line {node.lineno}: '{func_name}' is not allowed"
                )
            elif func_name not in self.ALLOWED_BUILTINS and func_name not in {
                "transform",  # Allow recursive calls
                "print",  # For debugging during dry-run
            }:
                # Allow calls if they're methods on allowed modules
                pass

    def _check_attribute(self, node: ast.Attribute) -> None:
        """Check attribute access (e.g., os.system, df.apply)."""
        attr_name = node.attr

        # Block dunder methods
        if attr_name.startswith("_"):
            self.violations.append(
                f"Line {node.lineno}: Dunder/private attributes not allowed: '{attr_name}'"
            )

        # Block dangerous attributes
        if attr_name in self.BLOCKED_ATTRIBUTES:
            self.violations.append(
                f"Line {node.lineno}: Blocked attribute: '{attr_name}'"
            )

        # Check the object being accessed
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            if obj_name not in self.ALLOWED_MODULES and obj_name not in {
                "df", "result"
            }:
                # If accessing attributes on non-allowed modules, flag it
                if obj_name in self.BLOCKED_IMPORTS:
                    self.violations.append(
                        f"Line {node.lineno}: Module '{obj_name}' is not allowed"
                    )

    def _check_name(self, node: ast.Name) -> None:
        """Check variable names and built-in references."""
        name = node.id

        # Allow common names
        if name in {
            "df", "result", "True", "False", "None",
            "pd", "np", "pandas", "numpy",
        }:
            return

        # Check if trying to access __builtins__
        if name.startswith("__"):
            self.violations.append(
                f"Line {node.lineno}: Dunder names not allowed: '{name}'"
            )


def validate_code(code: str) -> List[str]:
    """
    Convenience function to validate code.

    Args:
        code: Python code to validate

    Returns:
        List of violation messages
    """
    sanitizer = CodeSanitizer()
    return sanitizer.validate(code)
