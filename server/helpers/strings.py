def camel_case(name: str) -> str:
  """Convert snake_case names to CamelCase."""
  return "".join(part.capitalize() for part in name.split("_"))

