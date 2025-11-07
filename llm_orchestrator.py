"""
LLM Orchestrator for AI Transform.
Handles prompt building, provider calls, and code extraction.
"""

import os
import re
from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


class LLMOrchestrator:
    """Orchestrates LLM calls for code generation."""

    def __init__(self, vendor: str = "openai", model: str = None, temperature: float = 0.2):
        """
        Initialize the LLM orchestrator.

        Args:
            vendor: "openai" or "local"
            model: Model name (e.g., "gpt-4-turbo-preview")
            temperature: Temperature for generation (0.0 to 1.0)
        """
        self.vendor = vendor
        self.temperature = temperature

        if vendor == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key
            )
        else:
            raise ValueError(f"Vendor '{vendor}' not yet supported")

    def _build_system_prompt(self) -> str:
        """Build the system prompt for code generation."""
        return """You are an expert at writing safe, deterministic Pandas code.

Your task: Read the user's natural language description and write a single Python function called `transform(df)` that edits a single DataFrame.

Rules:
1. You MUST return ONLY a Python function definition. No imports, no explanations, no other code.
2. The function must be named `def transform(df):` and take exactly one argument: the input DataFrame.
3. Use only: `pd`, `np`, arithmetic, indexing, masks, groupby, agg, assign, rename operations.
4. NO imports, NO file/network I/O, NO eval/exec, NO plotting, NO OS access, NO subprocess calls.
5. Your function MUST return a modified DataFrame (or the original if no changes needed).
6. Handle edge cases gracefully (empty DataFrames, missing columns, etc.).
7. Be deterministic: same input → same output, always.

Example format:
```python
def transform(df):
    # Filter rows where 'column_name' > 100
    result = df[df['column_name'] > 100].copy()
    return result
```

Now, respond with ONLY the function code, wrapped in triple backticks."""

    def _build_context_message(self, schema: Dict[str, Any]) -> str:
        """Build context about the DataFrame schema."""
        context = f"""DataFrame Information:
- Shape: {schema['nrows']} rows × {len(schema['columns'])} columns
- Columns: {', '.join(schema['columns'])}
- Data Types:
{chr(10).join([f"  - {col}: {schema['dtypes'][col]}" for col in schema['columns']])}
- Null Rates:
{chr(10).join([f"  - {col}: {schema['null_rates'].get(col, 0):.1%}" for col in schema['columns']])}

Sample Values (first row):
{chr(10).join([f"  - {col}: {schema['sample_values'].get(col, 'N/A')}" for col in schema['columns']])}"""
        return context

    def generate_code(self, prompt: str, schema: Dict[str, Any]) -> str:
        """
        Generate Python code for a DataFrame transform.

        Args:
            prompt: Natural language description of the desired transformation
            schema: DataFrame schema information

        Returns:
            str: The generated `def transform(df):` function

        Raises:
            ValueError: If code generation fails or code validation fails
        """
        # Build messages
        system_msg = SystemMessage(content=self._build_system_prompt())
        context_msg = self._build_context_message(schema)
        user_content = f"{context_msg}\n\nUser Request:\n{prompt}"
        human_msg = HumanMessage(content=user_content)

        # Call LLM
        try:
            response = self.llm.invoke([system_msg, human_msg])
            full_response = response.content
        except Exception as e:
            raise ValueError(f"LLM call failed: {str(e)}")

        # Extract code from markdown block
        code = self._extract_code_block(full_response)
        if not code:
            raise ValueError("No Python code block found in LLM response")

        # Validate code structure
        self._validate_code_structure(code)

        return code

    def _extract_code_block(self, response: str) -> str:
        """Extract Python code from markdown code block."""
        # Try to find ```python ... ``` block
        match = re.search(r"```(?:python)?\s*(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # If no markdown block, assume the response is the code
        return response.strip()

    def _validate_code_structure(self, code: str) -> None:
        """
        Validate that code has the expected structure.

        Args:
            code: The code to validate

        Raises:
            ValueError: If code structure is invalid
        """
        if "def transform(df):" not in code:
            raise ValueError("Code must contain 'def transform(df):' function definition")

        # Try to parse as Python
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {str(e)}")


def get_available_vendors() -> List[str]:
    """Get list of available LLM vendors."""
    return ["openai"]  # Add "local" when implemented


def get_models_for_vendor(vendor: str) -> List[str]:
    """Get available models for a vendor."""
    if vendor == "openai":
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
    elif vendor == "local":
        return ["mistral", "llama2"]
    return []
