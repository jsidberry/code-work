import os
import re
import requests
from azure.identity import ManagedIdentityCredential
from azure.mgmt.containerregistry import ContainerRegistryManagementClient

# Function to get the 'meta.yml' file from a Bitbucket repository
def get_meta_yml_from_bitbucket(repo_owner, repo_slug, access_token):
    url = f"https://api.bitbucket.org/2.0/repositories/{repo_owner}/{repo_slug}/src/main/meta.yml"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to retrieve file from Bitbucket: {response.status_code} - {response.text}")

# Function to extract the version from the meta.yml file
def extract_version_from_meta_yml(meta_yml_content):
    version_line = next((line for line in meta_yml_content.splitlines() if line.startswith("version")), None)
    if version_line:
        match = re.search(r'\"(.*?)\"', version_line)
        if match:
            return match.group(1)
    raise Exception("Version not found in meta.yml")

# Function to get the tag of the image named 'bridge' in Azure Container Registry
def get_registry_version(registry_name, repository_name, image_name):
    credential = ManagedIdentityCredential()
    client     = ContainerRegistryManagementClient(credential, "<Your Azure Subscription ID>")
    registry   = client.registries.get(resource_group_name="<Your Resource Group>", registry_name=registry_name)

    tags_url   = f"https://{registry.login_server}/acr/v1/{repository_name}/_tags"
    response   = requests.get(tags_url, headers={"Authorization": f"Bearer {credential.get_token('https://management.azure.com/').token}"})
    if response.status_code == 200:
        tags = response.json().get("tags", [])
        for tag in tags:
            if tag.get("name") == image_name:
                return tag.get("tag")
    else:
        raise Exception(f"Failed to retrieve tags from Azure Container Registry: {response.status_code} - {response.text}")

# Function to compare the meta version with the registry version
def compare_versions(meta_version, reg_version):
    if meta_version == reg_version:
        print("Versions match.")
    else:
        print("Versions do not match.")

if __name__ == "__main__":
    # Bitbucket configuration
    repo_owner = "<Your Bitbucket Username>"
    repo_slug  = "<Your Bitbucket Repository Name>"
    bb_token   = "<Your Bitbucket Access Token>"

    # Azure configuration
    registry_name   = "<Your Azure Container Registry Name>"
    repository_name = "<Your ACR Repository Name>"
    image_name      = "bridge"

    # Step 1: Get the meta.yml file from Bitbucket
    meta_yml_content = get_meta_yml_from_bitbucket(repo_owner, repo_slug, bb_token)

    # Step 2: Extract the version from the meta.yml file
    meta_version = extract_version_from_meta_yml(meta_yml_content)

    # Step 3: Get the tag of the 'bridge' image from Azure Container Registry
    reg_version = get_registry_version(registry_name, repository_name, image_name)

    # Step 4: Compare the versions
    compare_versions(meta_version, reg_version)
