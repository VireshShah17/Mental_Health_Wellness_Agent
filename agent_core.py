# Import the required libraries
import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr
from prompt import sentiment_prompt


# Configure logging to INFO level by default
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S')

# Fetch and validate the Groq API key
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in the environment variables.")

# Initialize the Groq client with the API key and desired model parameters
llm = ChatGroq(api_key = SecretStr(GROQ_API_KEY), model = "llama-3.1-8b-instant", temperature = 0)

# Create the LangChain pipeline using the imported prompt
sentiment_chain = sentiment_prompt | llm


def analyze_sentiment(text):
    """
        Passes the text to the Groq agent and returns the sentiment.
    """
    try:
        response = sentiment_chain.invoke({"diary_text": text})
        return response.content.strip() # type: ignore
    except Exception as e:
        logging.error(f"Agent Analysis failed: {e}")
        return "Error"
