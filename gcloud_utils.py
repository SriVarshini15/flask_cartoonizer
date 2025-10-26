"""
Google Cloud Util Functions:
- Upload to Google Storage Bucket
- Delete from Google Storage Bucket
- Download file from Google Storage Bucket
- Generate signed URL
"""

import os
import datetime
from google.cloud import storage
from google.cloud.storage.blob import Blob

# Initialize Google Cloud Storage Client
client = storage.Client()

def upload_blob(bucket_name, source_file_name, destination_blob_name, content_type='', algo_unique_key=''):
    """
    Uploads a file to Google Cloud Storage Bucket.

    Args:
        bucket_name (str): Name of the GCS bucket
        source_file_name (str): Local path of the file to upload
        destination_blob_name (str): Desired name of the file in the bucket
        content_type (str, optional): MIME type of the file
        algo_unique_key (str, optional): Used for Algorithmia format URI

    Returns:
        str: GCS URI or Algorithmia-compatible URI
    """
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name, content_type=content_type)

    data_uri = blob.self_link.split("/")[-1]

    if algo_unique_key:
        return f"gs+{algo_unique_key}://{bucket_name}/{data_uri}"
    
    return f"gs://{bucket_name}/{data_uri}"

def delete_blob(bucket_name, blob_name):
    """
    Deletes a blob from the bucket.

    Args:
        bucket_name (str): GCS bucket name
        blob_name (str): Blob name to delete
    """
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    print(f"Blob {blob_name} deleted.")

def download_video(bucket_name, filename, output_filename):
    """
    Downloads a file from GCS to local path.

    Args:
        bucket_name (str): GCS bucket name
        filename (str): Blob name in the bucket
        output_filename (str): Local file path to save

    Returns:
        str: Local file path
    """
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.download_to_filename(output_filename)
    return output_filename

def generate_signed_url(output_uri):
    """
    Generates a signed URL for a blob.

    Args:
        output_uri (str): GCS URI of the blob (e.g., gs://bucket_name/file)

    Returns:
        str: Signed URL valid for download
    """
    expiration_time = datetime.timedelta(minutes=5)
    blob = Blob.from_string(output_uri, client=client)
    signed_url = blob.generate_signed_url(
        expiration=expiration_time,
        version='v4',
        response_disposition='attachment'
    )
    return signed_url
