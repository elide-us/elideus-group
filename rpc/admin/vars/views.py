from rpc.models import RPCResponse
from rpc.views import register_formatter
from .models import AdminVarsHostname1, AdminVarsHostnameViewDiscord1


@register_formatter("urn:admin:vars:hostname:1", "discord", "1")
def hostname_discord_v1(response: RPCResponse) -> RPCResponse:
  assert isinstance(response.payload, AdminVarsHostname1)
  payload = AdminVarsHostnameViewDiscord1(content=f"Hostname: {response.payload.hostname}")
  return RPCResponse(
    op=response.op,
    payload=payload,
    version=response.version,
    timestamp=response.timestamp,
    metadata=response.metadata,
  )

