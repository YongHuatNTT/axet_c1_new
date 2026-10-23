"""Output formatting helpers for logscope (JSON + Markdown report files)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union


def render_json(data: Dict[str, Any]) -> str:
    """Render a result dict as pretty-printed JSON."""
    return json.dumps(data, indent=2)


def generate_report_filename(command: str) -> str:
    """Build a deterministic markdown report filename for ``command``."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"logscope_{command}_{timestamp}.md"


def write_markdown_report(
    command: str,
    title: str,
    body_lines: List[str],
    output_dir: Union[str, Path] = ".",
) -> Path:
    """Write a markdown report file and return its path."""
    output_path = Path(output_dir) / generate_report_filename(command)
    content = f"# {title}\n\n" + "\n".join(body_lines) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path
