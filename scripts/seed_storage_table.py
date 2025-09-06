from __future__ import annotations
import asyncio, os
from typing import Dict, Set, Tuple
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from scriptlib import connect

async def _fetch_type_map(conn) -> Dict[str, int]:
  async with conn.cursor() as cur:
    await cur.execute("SELECT recid, element_mimetype FROM storage_types")
    rows = await cur.fetchall()
  return {m: recid for recid, m in rows}

async def _fetch_user_guids(conn) -> Set[str]:
  async with conn.cursor() as cur:
    await cur.execute("SELECT element_guid FROM account_users")
    rows = await cur.fetchall()
  return {r[0] for r in rows}

async def _get_container(conn) -> Tuple[BlobServiceClient, ContainerClient]:
  async with conn.cursor() as cur:
    await cur.execute(
      "SELECT element_value FROM system_config WHERE element_key=?",
      ("AzureBlobContainerName",),
    )
    row = await cur.fetchone()
    if not row:
      raise RuntimeError("AzureBlobContainerName missing from config")
    container = row[0]
  dsn = os.getenv("AZURE_BLOB_CONNECTION_STRING")
  if not dsn:
    raise RuntimeError("AZURE_BLOB_CONNECTION_STRING not set")
  bsc = BlobServiceClient.from_connection_string(dsn)
  return bsc, bsc.get_container_client(container)

async def seed_storage_cache():
  conn = await connect()
  conn.autocommit = False
  bsc: BlobServiceClient | None = None
  container: ContainerClient | None = None
  try:
    bsc, container = await _get_container(conn)
    type_map = await _fetch_type_map(conn)
    user_guids = await _fetch_user_guids(conn)
    octet_type = type_map.get("application/octet-stream")
    async for blob in container.list_blobs():
      name = getattr(blob, "name", None)
      if not name:
        continue
      parts = name.split("/")
      if len(parts) < 2:
        continue
      user_guid = parts[0]
      if user_guid not in user_guids:
        continue
      if parts[-1] == ".init":
        continue
      path = "/".join(parts[1:-1])
      filename = parts[-1]
      ct = getattr(blob, "content_type", None)
      if not ct and hasattr(blob, "content_settings"):
        ct = getattr(blob.content_settings, "content_type", None)
      mimetype = ct or "application/octet-stream"
      types_recid = type_map.get(mimetype, octet_type)
      async with conn.cursor() as cur:
        await cur.execute(
          "SELECT 1 FROM users_storage_cache WHERE users_guid=? AND element_path=? AND element_filename=?",
          (user_guid, path, filename),
        )
        if await cur.fetchone():
          continue
        await cur.execute(
          "INSERT INTO users_storage_cache (users_guid, types_recid, element_path, element_filename, element_public, element_deleted) VALUES (?, ?, ?, ?, 0, 0)",
          (user_guid, types_recid, path, filename),
        )
    await conn.commit()
  finally:
    if container:
      await container.close()
    if bsc:
      await bsc.close()
    await conn.close()

if __name__ == "__main__":
  asyncio.run(seed_storage_cache())
