from flask import Flask, request, render_template_string
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# === Key Vault config ===
KEY_VAULT_URL = "https://keyvault-wayver.vault.azure.net"  # Replace with your Key Vault name
SECRET_NAME = "StorageConnStr"  # The secret name in Key Vault

# Authenticate with Managed Identity
try:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    conn_str = secret_client.get_secret(SECRET_NAME).value
except Exception as e:
    print("Failed to get secret:", e)
    conn_str = None

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

@app.route("/list")
def list_files():
    account_url = "https://<your-storage-account>.blob.core.windows.net"
    container_name = "<your-container>"

    blob_service_client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
    container_client = blob_service_client.get_container_client(container_name)

    files = [blob.name for blob in container_client.list_blobs()]
    return {"files": files}

@app.route("/delete", methods=["POST"])
def delete_file():
    blob_name = request.json.get("filename")
    if not blob_name:
        return jsonify({"error": "filename is required"}), 400

    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        return jsonify({"message": f"{blob_name} deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  
    app.run(host="0.0.0.0", port=port, debug=True)
