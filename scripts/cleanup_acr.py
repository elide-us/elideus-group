import datetime
from azure.identity import DefaultAzureCredential
from azure.containerregistry import ContainerRegistryClient

# Env var required:
ACR_LOGIN_SERVER = "elideus.azurecr.io"
CLEANUP_DAYS = 2

def main():
  login_server = ACR_LOGIN_SERVER
  credential = DefaultAzureCredential()
  client = ContainerRegistryClient(endpoint=login_server, credential=credential)

  cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=CLEANUP_DAYS)

  for repository in client.list_repository_names():
    print(f"\nChecking repository: {repository}")
    for manifest in client.list_manifest_properties(repository=repository):
      digest = manifest.digest
      created_on = manifest.created_on
      tags = manifest.tags or []

      if created_on and created_on < cutoff:
        print(f"  Deleting {repository}@{digest} (created {created_on})")
        client.delete_manifest(repository=repository, tag_or_digest=digest)
      if not tags:
        print(f"  Deleting untagged manifest {repository}@{digest}")
        try:
          client.delete_manifest(repository=repository, tag_or_digest=digest)
        except Exception as e:
          print(f"    Failed to delete {digest}: {e}")
  print("\nCleanup complete.")

if __name__ == "__main__":
  main()
