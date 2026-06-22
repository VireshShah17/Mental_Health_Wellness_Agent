from langchain_core.prompts import PromptTemplate

# --- THE DIGITAL THERAPIST PROMPT ---
sentiment_template = """
        You are a digital therapist analyzing a diary entry. 
        Read the following text and determine if the overall sentiment is Positive or Negative.
        Respond with ONLY the word "Positive" or "Negative". Do not include any other text.

        Diary Entry:
        {diary_text}

        Sentiment:
    """

sentiment_prompt = PromptTemplate(
    input_variables = ["diary_text"],
    template = sentiment_template
)
