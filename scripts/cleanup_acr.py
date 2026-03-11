"""Cleanup old container images from Azure Container Registry.

Prerequisites:
  1. Install the Azure Developer CLI:
       winget install microsoft.azd

  2. Authenticate to Azure:
       azd auth login

  3. Ensure your account has permissions to the container registry
     (AcrDelete role on the registry resource).

Usage:
  python scripts/cleanup_acr.py

The script connects to the ACR using DefaultAzureCredential, which
will use the credentials from 'azd auth login' (or az cli, environment
variables, managed identity, etc. in standard precedence order).

Images older than CLEANUP_DAYS (default: 2) are deleted, except for
the most recent manifest in each repository which is always preserved.
Untagged manifests are also cleaned up.
"""

import datetime
from azure.identity import DefaultAzureCredential
from azure.containerregistry import ContainerRegistryClient

# Env var required:
ACR_LOGIN_SERVER = "elideus.azurecr.io"
CLEANUP_DAYS = 2

def main():
  login_server = ACR_LOGIN_SERVER

  try:
    credential = DefaultAzureCredential()
    client = ContainerRegistryClient(endpoint=login_server, credential=credential)
    repositories = list(client.list_repository_names())
  except Exception as e:
    print(f"Authentication failed: {e}")
    print()
    print("To fix this, set up your Azure credentials:")
    print()
    print("  1. Install the Azure Developer CLI:")
    print("       winget install microsoft.azd")
    print()
    print("  2. Authenticate to Azure:")
    print("       azd auth login")
    print()
    print("  3. Ensure your account has the AcrDelete role on the registry.")
    print()
    print(f"  Registry: {login_server}")
    return

  cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=CLEANUP_DAYS)

  for repository in repositories:
    print(f"\nChecking repository: {repository}")
    manifests = sorted(
       list(client.list_manifest_properties(repository=repository)),
       key = lambda m: m.created_on or datetime.datetime.min,
       reverse = True
    )

    if not manifests:
       continue

    newest_digest = manifests[0].digest
    for manifest in manifests:
      digest = manifest.digest
      created_on = manifest.created_on
      tags = manifest.tags or []

      if digest == newest_digest:
         print(f"Skipping most recent manifest {repository}@{digest}")
         continue
      if created_on and created_on < cutoff:
        print(f"  Deleting {repository}@{digest} (created {created_on})")
        client.delete_manifest(repository=repository, tag_or_digest=digest)
      elif not tags:
        print(f"  Deleting untagged manifest {repository}@{digest}")
        try:
          client.delete_manifest(repository=repository, tag_or_digest=digest)
        except Exception as e:
          print(f"    Failed to delete {digest}: {e}")
  print("\nCleanup complete.")

if __name__ == "__main__":
  main()
