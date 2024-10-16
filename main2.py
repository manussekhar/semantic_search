import json
import uuid

from flask import Flask, request, jsonify, render_template, render_template_string
import logging
import traceback
import shutil
import pandas as pd
import os
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client import models
from waitress import serve

from dotenv import load_dotenv

load_dotenv()

JOB_NAME = 'Job Name'
INCIDENT_ID = 'Incident ID'
WORK_DETAILS = 'Work Details'
NOTES = 'Notes'
SUMMARY = 'Summary'
REPORTED_DATE = 'Reported Date'
RESOLVED_DATE = 'Resolved Date'
RESOLUTION = 'Resolution'
SUBMIT_DATE = 'Submit Date'
SUBMITTER_NAME = 'Submitter Name'
SUBMITTER = 'Submitter'
STATUS = 'Status'
ASSIGNEE = 'Assignee'
ASSIGNED_GROUP = 'Assigned Group'
FLAG = 'Flag'
MQ = 'MQ'
JOB = 'job'
DONE = 'done'

collections = [
    JOB_NAME,
    INCIDENT_ID,
    WORK_DETAILS,
    NOTES,
    SUMMARY,
    REPORTED_DATE,
    RESOLVED_DATE,
    RESOLUTION,
    SUBMIT_DATE,
    SUBMITTER_NAME,
    SUBMITTER,
    STATUS,
    ASSIGNEE,
    ASSIGNED_GROUP,
    FLAG,
    MQ,
    JOB,
    DONE
]
# Initialize cache
embeddings_cache = {}

# Initialize Flask app
app = Flask(__name__)
logger = logging.getLogger('semantic_search')

def setup_logging():
    # Configure logging
    logger.setLevel(logging.INFO)
    # Create handlers
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # Create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


setup_logging()

# Initialize Qdrant client and collection


def get_embeddings(text):
    logger.info(f"Generating embeddings for text: {text}...")
    if text in embeddings_cache:
        logger.info("Returning cached embeddings.")
        return embeddings_cache[text]

    try:
        oaclient = OpenAI()
        response = oaclient.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embeddings = response.data[0].embedding
        embeddings_cache[text] = embeddings
        logger.info("Embeddings generated and cached successfully.")
        return embeddings
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

# Route to serve the index.html file
@app.route('/')
def index():
    return render_template('index.html')

# HTMX route to send a message back
@app.route('/hello', methods=['GET'])
def hello():
    # This will return a small HTML snippet
    return render_template_string('<p>Hello from the server!</p>')

@app.route('/update', methods=['GET'])
def update():
    try:
        # Check if the directory exists before attempting to delete it
        if os.path.exists('./qdrant_data'):
            shutil.rmtree('./qdrant_data')

        client = QdrantClient(path="./qdrant_data")

        for collection_name in collections:
            create_collection(client, collection_name)


        df = pd.read_excel('./Data/polisy/Data.xlsx')
        logger.info("Excel file loaded successfully.")
        for index, row in df.iterrows():
            id = str(uuid.uuid4())
            for collection_name in collections:
                insert(client, id, row, collection_name)
        logger.info("Data loaded successfully into Qdrant.")
        return jsonify({"message": "Data updated successfully"}), 200
    except Exception as e:
        print(traceback.format_exc())
        logger.error(f"Error loading data: {e}")
        return jsonify({"error": str(e)}), 500


def insert(client, id, row, collection_name):
    metadata = row[collection_name]
    json_object = json.loads(row.to_json())
    # Check if id or metadata is null or empty
    if pd.isnull(metadata) or metadata == '':
        logger.warning(f"Skipping row {index} due to null or empty ID or METADATA.")
        return None
    embedding = get_embeddings(metadata)
    logger.info(f"upserting data: {metadata[:30]}...")
    client.upsert(
        collection_name=collection_name,
        points=[
            models.PointStruct(
                id=id,
                vector=embedding,
                payload=json_object
            )
        ]
    )
    logger.info(f"Completed upserting data: {metadata[:30]}...")


def create_collection(client, collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
    )
    logger.info(f"Qdrant collection created for {collection_name}.")

@app.route('/search', methods=['GET'])
def search():
    try:
        query_params = request.args
        logger.info(f"Received search query parameters: {query_params}")
        collection_names = [key for key in query_params if key in collections]
        if not collection_names:
            logger.warning("query parameter is wrong.")
            return jsonify({"error": "query parameter is wrong"}), 400

        # Get the matching key and its value
        collection_name = collection_names[0]
        query = query_params[collection_name]
        query_vector = get_embeddings(query)
        client = QdrantClient(path="./qdrant_data")
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=20
        )
        responses = []
        for response in results:
            responses.append(response.payload)

        logger.info(f"Search completed successfully with {len(responses)} results.")
        return jsonify(responses)
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting semantic search app.")
    serve(app, host='0.0.0.0', port=5000)
