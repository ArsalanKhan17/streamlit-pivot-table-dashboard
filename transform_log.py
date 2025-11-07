"""
Transform Log for AI Transform.
Tracks transformation history and enables undo functionality.
"""

import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import pandas as pd
import uuid


@dataclass
class TransformStep:
    """Represents a single transformation step."""

    id: str
    ts: str  # ISO8601 timestamp
    prompt: str
    code_hash: str
    schema_before: Dict[str, Any]
    schema_after: Dict[str, Any]
    diff: Dict[str, Any]
    code: Optional[str] = None  # Full code for reproducibility

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TransformStep":
        """Create from dictionary."""
        return TransformStep(**data)


class TransformLog:
    """Manages transformation history."""

    def __init__(self):
        """Initialize the transform log."""
        self.steps: List[TransformStep] = []
        self.df_snapshots: Dict[str, pd.DataFrame] = {}  # Map of step_id to DataFrame state

    def append(
        self,
        prompt: str,
        code: str,
        diff: Dict[str, Any],
        schema_before: Dict[str, Any],
        schema_after: Dict[str, Any],
        df_after: Optional[pd.DataFrame] = None,
    ) -> None:
        """
        Append a transformation step to the log.

        Args:
            prompt: User's natural language prompt
            code: Generated Python code
            diff: Diff dictionary from compute_diff
            schema_before: Schema snapshot before transformation
            schema_after: Schema snapshot after transformation
            df_after: Optional DataFrame to store for potential undo
        """
        step_id = str(uuid.uuid4())
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        ts = datetime.utcnow().isoformat()

        step = TransformStep(
            id=step_id,
            ts=ts,
            prompt=prompt,
            code_hash=code_hash,
            schema_before=schema_before,
            schema_after=schema_after,
            diff=diff,
            code=code,
        )

        self.steps.append(step)

        # Store DataFrame snapshot for undo
        if df_after is not None:
            self.df_snapshots[step_id] = df_after.copy()

    def undo_last(self) -> Optional[str]:
        """
        Undo the last transformation.

        Returns:
            Step ID of the previous state (before the last transform), or None
        """
        if len(self.steps) < 2:
            return None

        # Remove the last step
        last_step = self.steps.pop()

        # Return the ID of what is now the last step
        # (or None if no more steps)
        if self.steps:
            return self.steps[-1].id
        return None

    def get_df_for_step(self, step_id: str) -> Optional[pd.DataFrame]:
        """Get the DataFrame state after a specific step."""
        return self.df_snapshots.get(step_id)

    def export_manifest_json(self) -> str:
        """
        Export transform log as JSON manifest.

        Returns:
            JSON string
        """
        manifest = {
            "export_date": datetime.utcnow().isoformat(),
            "version": "1.0",
            "transform_count": len(self.steps),
            "steps": [step.to_dict() for step in self.steps],
        }
        return json.dumps(manifest, indent=2, default=str)

    def export_recipe_py(self) -> str:
        """
        Export transformation recipe as executable Python code.

        Returns:
            Python code that can be run standalone
        """
        lines = [
            "#!/usr/bin/env python",
            '"""',
            "AI Transform Recipe",
            f"Generated: {datetime.utcnow().isoformat()}",
            f"Total transforms: {len(self.steps)}",
            '"""',
            "",
            "import pandas as pd",
            "import numpy as np",
            "",
        ]

        # Add each transformation as a separate function
        for i, step in enumerate(self.steps, 1):
            lines.append(f"# Transform {i}: {step.ts}")
            lines.append(f"# Prompt: {step.prompt[:100]}")
            lines.append("# " + "-" * 60)
            lines.append(step.code)
            lines.append("")

        # Add main function that chains all transforms
        lines.append("def apply_all_transforms(df):")
        lines.append('    """Apply all transforms in sequence."""')
        for i in range(1, len(self.steps) + 1):
            lines.append(f"    # Step {i}")
            lines.append(f"    df = transform_{i}(df)")
        lines.append("    return df")
        lines.append("")
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    # Load your CSV here")
        lines.append("    df = pd.read_csv('your_file.csv')")
        lines.append("    result = apply_all_transforms(df)")
        lines.append("    result.to_csv('output.csv', index=False)")

        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert log to a DataFrame for display.

        Returns:
            DataFrame with transform history
        """
        records = []
        for step in self.steps:
            records.append({
                "Timestamp": step.ts,
                "Prompt": step.prompt[:50] + "..." if len(step.prompt) > 50 else step.prompt,
                "Code Hash": step.code_hash[:8],
                "Rows Δ": step.diff.get("rows_delta", 0),
                "Cols Added": len(step.diff.get("cols_added", [])),
                "Cols Removed": len(step.diff.get("cols_removed", [])),
            })

        return pd.DataFrame(records)

    def __len__(self) -> int:
        """Get number of steps in log."""
        return len(self.steps)

    def __getitem__(self, index: int) -> TransformStep:
        """Get a step by index."""
        return self.steps[index]
