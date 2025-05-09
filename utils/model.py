from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv('.env')

def load_openai_model():
    model = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0
    )

    return model
