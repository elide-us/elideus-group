def camel_case(name: str) -> str:
  """Convert snake_case names to CamelCase."""
  return "".join(part.capitalize() for part in name.split("_"))



import uuid

DETERMINISTIC_NS = uuid.UUID('DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67')

def deterministic_guid(entity_type: str, natural_key: str) -> str:
  """Compute a deterministic UUID5 from the platform namespace.

  Formula: uuid5(DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67, '{entity_type}:{natural_key}')
  Returns uppercase string with hyphens.
  """
  return str(uuid.uuid5(DETERMINISTIC_NS, f'{entity_type}:{natural_key}')).upper()
