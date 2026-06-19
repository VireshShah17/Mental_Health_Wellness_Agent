# Import the required libraries
import logging
import re
import docx
import os
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from drive_auth import authenticate_google_drive, download_docx_from_drive
from weather_checker import get_weather_for_date


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

# LangChain Prompt to enforce strict "Positive" or "Negative" output
sentiment_prompt = PromptTemplate(
    input_variables = ["diary_text"],
    template = """
            You are a digital therapist analyzing a diary entry.
            Read the following text and determine if the overall sentiment is Positive or Negative.
            Respond with ONLY the word "Positive" or "Negative". Do not include any other text.
            
            Diary Entry:
            {diary_text}
            
            Sentiment:
    """
)

sentiment_chain = sentiment_prompt | llm


def parse_docx_diaries(file_path):
    """
        Reads a .docx file and extracts dates and diary entries.
    """

    if not os.path.exists(file_path):
        logging.error(f"===== File not found: {file_path} =====")
        return []
    
    doc = docx.Document(file_path)
    full_text = "\n".join([para.text for para in doc.paragraphs])

    # Regex to match: Diary_YYYY_MM_DD : "text"
    pattern = r'Diary_(\d{4}_\d{2}_\d{2})\s*:\s*["“”](.*?)["“”]'
    matches = re.finditer(pattern, full_text, re.DOTALL)
    
    entries = []
    for match in matches:
        raw_date = match.group(1)
        formatted_date = raw_date.replace('_', '-')
        text_content = match.group(2).strip()

        entries.append({
            "date": formatted_date,
            "text": text_content
        })
        logging.info(f"===== Successfully extracted entry for date: {formatted_date} =====")
    
    return entries


def run_analysis_pipeline(entries, weather_file_path):
    """
        Processes entries through the Groq LLM AND checks the weather.
    """
    analyzed_results = []

    for entry in entries:
        date = entry["date"]
        logging.info(f"===== Analyzing sentiment and weather for {date}... =====")

        try:
            # Get the sentiment
            response = sentiment_chain.invoke({"diary_text": entry['text']})
            sentiment = response.content.strip() # type: ignore

            # Get the weather
            weather_condition = get_weather_for_date(date, weather_file_path)

            # Combine Data
            analyzed_results.append({
                "date": date,
                "sentiment": sentiment,
                "weather": weather_condition
            })

        except Exception as e:
            logging.error(f"===== Analysis failed for {date}: {e} =====")
            
    return analyzed_results


if __name__ == '__main__':
    TARGET_FILE = 'Agent Data'
    WEATHER_FILE = 'Open-Meteo API (JSON Responses).json'
    
    # 1. Authenticate and Download (using drive_auth.py)
    service = authenticate_google_drive()
    local_file_path = download_docx_from_drive(service, TARGET_FILE)
    
    if local_file_path:
        # 2. Parse the downloaded file
        logging.info("===== Parsing data... =====")
        diary_entries = parse_docx_diaries(local_file_path)
        
        if diary_entries:
            # 3. Analyze Sentiment
            logging.info(f"===== Running Groq analysis on {len(diary_entries)} entries... =====")
            final_results = run_analysis_pipeline(diary_entries, WEATHER_FILE)
            
            logging.info("--- FINAL SENTIMENT DATA ---")
            for res in final_results:
                print(f"- {res['date']} | Sentiment: {res['sentiment']} | Weather: {res['weather']}")
                
        # 4. Clean up the temporary file from your Ubuntu system
        os.remove(local_file_path)
        logging.info("Cleaned up temporary local file.")
