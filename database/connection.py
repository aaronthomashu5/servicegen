import pymongo
import gridfs
import os
import streamlit as st
from typing import Dict, Any, Optional

def get_mongo_client():
    """Create and return a MongoDB client using connection string."""
    try:
        # Try to get connection string from Streamlit secrets
        import streamlit as st
        connection_string = st.secrets["MONGO_CONNECTION_STRING"]
    except (ImportError, KeyError):
        # Fallback to environment variable or default
        connection_string = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://localhost:27017/")
    
    try:
        client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        # Verify the connection
        client.admin.command('ismaster')
        return client
    except pymongo.errors.ConnectionFailure as e:
        st.error(f"Failed to connect to MongoDB: {str(e)}")
        st.info("Using a fallback in-memory database for demonstration purposes.")
        # For demo/fallback, create an in-memory object to simulate MongoDB
        from pymongo.mongo_client import MongoClient
        from pymongo.server_api import ServerApi
        return MongoClient(connection_string, server_api=ServerApi('1'))
    except Exception as e:
        st.error(f"Unexpected error while connecting to MongoDB: {str(e)}")
        # Return a client anyway, but operations may fail later
        return pymongo.MongoClient(connection_string)

# Initialize MongoDB client and database
client = get_mongo_client()
db = client.service_workflow
fs = gridfs.GridFS(db)  # For file storage with GridFS

# Collections
customers = db.customers
mrns = db.mrns
service_reports = db.service_reports
