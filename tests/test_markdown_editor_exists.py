import os


def test_markdown_editor_component_exists():
  path = os.path.join("frontend", "src", "components", "MarkdownEditor.tsx")
  assert os.path.isfile(path), f"MarkdownEditor.tsx not found at {path}"
