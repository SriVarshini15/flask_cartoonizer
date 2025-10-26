import Algorithmia

# Read the Algorithmia API key from a file
with open("algo.txt", "r") as infile:
    client_key = infile.read().strip()

# Initialize the Algorithmia client
client = Algorithmia.client(client_key)

# Set up the specific algorithm for cartoonizing
algo = client.algo('tjdevworks/cartoonizer/2.2.2')
algo.set_options(timeout=300)

def api_request(input_file_uri):
    """
    Send a video URI to Algorithmia cartoonizer and return the result.

    Args:
        input_file_uri (str): The URI of the uploaded video in cloud storage.

    Returns:
        dict: A response containing the cartoonized video URL.
    """
    input_payload = {
        "data_uri": input_file_uri,
        "data_type": 1,
        "datastore": ""
    }

    response = algo.pipe(input_payload).result
    return response
