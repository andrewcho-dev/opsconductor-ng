"""JSON Schema generation for OpsConductor NG contracts."""

import json
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel

from .models import (
    UserIntent,
    SelectedTool,
    Step,
    ExecutionPlan,
    StepResult,
    RunResult,
)


def generate_schemas(output_dir: Optional[str | Path] = None) -> None:
    """Generate JSON schemas for all contract models.
    
    Args:
        output_dir: Directory to write schema files to. Defaults to shared/schemas/
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "schemas"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    models: list[Type[BaseModel]] = [
        UserIntent,
        SelectedTool,
        Step,
        ExecutionPlan,
        StepResult,
        RunResult,
    ]
    
    for model in models:
        schema = model.model_json_schema()
        schema_file = output_dir / f"{model.__name__}.json"
        
        with open(schema_file, "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"Generated schema: {schema_file}")


if __name__ == "__main__":
    generate_schemas()