# Create a new Pinecone index
pinecone.init(api_key="api", environment="env")
index_name = "index"
pinecone.create_index(index_name)

# Retrieve data from your Notion database
# For example, if you're using the notion-client library:
from notion_client import Client

notion = Client(auth="api")
db = notion.databases.retrieve(database_id="databaseid")
results = db.query()

# Add the text data to the Pinecone index
for result in results:
    text_data = result.properties["text"].title[0].plain_text
    pinecone.upsert(index_name=index_name, data={"text": text_data})
