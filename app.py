from flask import Flask, request, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# === Key Vault config ===
KEY_VAULT_URL = "https://keyvault-wayver.vault.azure.net"  # Replace with your Key Vault name
SECRET_NAME = "StorageConnStr"  # The secret name in Key Vault

# Authenticate with Managed Identity
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
conn_str = secret_client.get_secret(SECRET_NAME).value

# Blob storage client
blob_service_client = BlobServiceClient.from_connection_string(conn_str)
CONTAINER_NAME = "uploads"

# Flask route
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        f = request.files["file"]
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=f.filename)
        blob_client.upload_blob(f, overwrite=True)
        return "File uploaded!"
    return render_template_string('''
        <h2>Upload a File</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    ''')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
