from __future__ import annotations
import asyncio
import os
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from scriptlib import connect


def _debug(msg: str):
  print(msg, flush=True)

async def _fetch_type_map(conn) -> dict[str, int]:
  async with conn.cursor() as cur:
    await cur.execute("SELECT recid, element_mimetype FROM storage_types")
    rows = await cur.fetchall()
  return {m: recid for recid, m in rows}

async def _fetch_user_guids(conn) -> set[str]:
  async with conn.cursor() as cur:
    await cur.execute("SELECT element_guid FROM account_users")
    rows = await cur.fetchall()
  return {r[0] for r in rows}

async def _show_cache_sample(conn, limit: int = 5) -> None:
  async with conn.cursor() as cur:
    await cur.execute(
      f"SELECT TOP ({limit}) users_guid, element_path, element_filename, element_mimetype, element_displaytype FROM vw_users_storage_cache ORDER BY recid DESC",
    )
    rows = await cur.fetchall()
  _debug("recent cache rows:")
  for guid, path, filename, mimetype, display in rows:
    full_path = f"{path}/{filename}" if path else filename
    _debug(f"  {guid} | {full_path} | {mimetype} | {display}")

async def _get_container(conn) -> tuple[BlobServiceClient, ContainerClient]:
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
  _debug("connected to database")
  conn.autocommit = False
  bsc: BlobServiceClient | None = None
  container: ContainerClient | None = None
  try:
    bsc, container = await _get_container(conn)
    _debug("connected to storage container")
    type_map = await _fetch_type_map(conn)
    _debug(f"loaded {len(type_map)} mime types")
    user_guids = await _fetch_user_guids(conn)
    _debug(f"loaded {len(user_guids)} user guids")
    octet_type = type_map.get("application/octet-stream")
    inserted = 0
    async for blob in container.list_blobs():
      name = getattr(blob, "name", None)
      if not name:
        _debug("skipping blob with no name")
        continue
      parts = name.split("/")
      if len(parts) < 2:
        _debug(f"skipping {name}: not enough path parts")
        continue
      user_guid = parts[0]
      if user_guid not in user_guids:
        _debug(f"skipping {name}: unknown user {user_guid}")
        continue
      if parts[-1] == ".init":
        _debug(f"skipping {name}: init marker")
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
          _debug(f"skipping {name}: already exists")
          continue
        await cur.execute(
          "INSERT INTO users_storage_cache (users_guid, types_recid, element_path, element_filename, element_public, element_deleted) VALUES (?, ?, ?, ?, 0, 0)",
          (user_guid, types_recid, path, filename),
        )
        inserted += 1
    await conn.commit()
    _debug(f"inserted {inserted} records")
    await _show_cache_sample(conn)
  finally:
    if container:
      await container.close()
    if bsc:
      await bsc.close()
    await conn.close()

if __name__ == "__main__":
  asyncio.run(seed_storage_cache())
