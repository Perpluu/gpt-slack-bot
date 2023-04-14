# Import necessary libraries and modules
import slack_sdk
import pinecone
import langchain
import openai
import notion_client
import re
from dotenv import load_dotenv
import os

load_dotenv()

your_pinecone_api_key = os.environ.get('pinecone')
your_openai_api_key = os.environ.get('openai')
your_notion_api_key = os.environ.get('notion')

# Set up Pinecone client and index
pinecone.init(api_key=your_pinecone_api_key)
index = pinecone.Index(index_name="your_index_name")

langchain_client = langchain.Client()

# Set up ChatGPT client
openai.api_key = your_openai_api_key

# Set up Notion client and database
notion = notion_client.Client(auth=your_notion_api_key)
database_id = "your_database_id"

# Set up Slack bot and event listener
slack_bot = slack_sdk.WebClient(token="your_slack_bot_token")
SLACK_BOT_ID = slack_bot.api_call("auth.test")["user_id"]

def parse_bot_commands(slack_events):
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == SLACK_BOT_ID:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    matches = re.search("^<@(|[WU].+?)>(.*)", message_text)
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

# Define a function to retrieve Notion data
def retrieve_notion_data(database_id):
    # Retrieve data from Notion
    database = notion.databases.retrieve(database_id)
    results = notion.databases.query(
        **{
            "database_id": database_id,
        }
    ).get("results")
    return results

# Define a function to search Pinecone index
def search_pinecone_index(query, language):
    # Search for similar data in Pinecone index
    embeddings = langchain_client.embed(text=query, language=language)
    results = index.query(queries=embeddings, top_k=1)
    return results[0]

# Define a function to generate a natural language response using ChatGPT
def generate_chatgpt_response(query):
    # Generate response using ChatGPT
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=query,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return response.choices[0].text.strip()

# Define a function to handle user queries
def handle_query(query):
    # Detect language of query
    language = langchain_client.detect(query)
    # Search Pinecone index for relevant data
    data = search_pinecone_index(query, language)
    # Retrieve data from Notion
    notion_data = retrieve_notion_data(database_id)
    # Use ChatGPT to generate response
    response = generate_chatgpt_response(query)
    return response

# Define a function to send response to Slack
def send_slack_response(response, channel):
    slack_bot.api_call("chat.postMessage", channel=channel, text=response)

# Define the main function to handle events
def main():
    if slack_bot.rtm_connect(with_team_state=False):
        print("Bot connected and running!")
        while True:
            query, channel = parse_bot_commands(slack_bot.rtm_read())
            if query:
                response = handle_query(query)
                send_slack_response(response, channel)
    else:
        print("Bot failed to connect!")

