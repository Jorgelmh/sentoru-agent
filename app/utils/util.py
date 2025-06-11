from pathlib import Path


def load_prompt(prompt_name: str) -> str:
    """Loads a prompt from the prompts directory."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / f"{prompt_name}.md"
    with open(prompt_path) as f:
        return f.read()
