from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from typing import Any
import requests
import math
import os
import sqlite3
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from JinaEmbeddings import JinaEmbeddings
from langchain_community.vectorstores import FAISS
from langgraph.types import interrupt,Command


load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0.7,
)

embeddings = JinaEmbeddings(api_key=os.getenv("JINA_API_KEY"))


def ingest_rag_document(file_path):
    DB_PATH = "faiss_db"
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(DB_PATH)


def get_retriever():
    DB_PATH = "faiss_db"
    vector_store = FAISS.load_local(
            folder_path=DB_PATH,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
    
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    return retriever

# rag tool

@tool
def rag_tool(query: str) -> str:
    """
    Retrieve relevant information from the PDF document.

    Use this tool when the user asks factual or conceptual questions
    that may be answered using the stored PDF documents.

    Args:
        query: The question or search query used to retrieve PDF content.
    """
    retriever = get_retriever()
    documents = retriever.invoke(query)

    if not documents:
        return "No relevant information was found in the PDF."

    formatted_documents = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "Unknown source")
        page = document.metadata.get("page", "Unknown page")

        formatted_documents.append(
            f"Document {index}\n"
            f"Source: {source}\n"
            f"Page: {page}\n"
            f"Content: {document.page_content}"
        )

    return "\n\n".join(formatted_documents)


# Tools
search_tool = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="advanced"
)


@tool
def calculator(expression: str) -> str:
    """
    Useful for simple math calculations.
    Input should be a valid math expression.
    Example: 2 + 2, math.sqrt(16), 10 * 5
    """

    try:
        allowed = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum
        }

        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)

    except Exception as e:
        return f"Calculation error: {str(e)}"



@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('VANTAGE_API_KEY')}"
    r = requests.get(url)
    return r.json()


@tool
def get_weather(location: str) -> dict:
    """Get weather information for a given location."""
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    API_KEY = os.getenv("WEATHER_API_KEY")
    params = {
        "q": location,
        "appid": API_KEY,
        "units": "metric"
    }
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()

    data = r.json()

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "weather": data["weather"][0]["main"],
        "description": data["weather"][0]["description"]
    }


@tool
def purchase_stock(symbol: str, quantity: int) -> dict:
    """
    Simulate purchasing a stock. This is a mock function and does not perform real transactions.
    HUMAN-IN-THE-LOOP (HITL):
    Before confirming the purchase, the tool will interrupt and wait for the human decision (Yes/Anything else).
    """
    decision = interrupt(f"Approve buying {quantity} shares of {symbol}?")

    if isinstance(decision, str) and decision.lower() == "yes":
        return {"status": "success", "message": f"Purchased {quantity} shares of {symbol}"}
    else:
        return {"status": "failure", "message": "Declined purchase"}


@tool
def sell_stock(symbol: str, quantity: int) -> dict:
    """
    Simulate selling a stock. This is a mock function and does not perform real transactions.
    HUMAN-IN-THE-LOOP (HITL):
    Before confirming the sale, the tool will interrupt and wait for the human decision (Yes/Anything else).
    """
    decision = interrupt(f"Approve selling {quantity} shares of {symbol}?")

    if isinstance(decision, str) and decision.lower() == "yes":
        return {"status": "success", "message": f"Sold {quantity} shares of {symbol}"}
    else:
        return {"status": "failure", "message": "Declined sale"}


# Make tool list
tools = [search_tool,calculator, get_stock_price,get_weather,rag_tool,purchase_stock,sell_stock]

# Make the LLM tool-aware
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# graph nodes
def chat_node(state: ChatState):
    """LLM node that can answer directly or call an appropriate tool."""

    system_message = SystemMessage(
        content=(
            "You are a helpful Agentic Chatbot with access to several tools.\n\n"

            "Tool usage instructions:\n"
            "- Use `rag_tool` for questions about the uploaded PDF or document. "
            "Always retrieve relevant document content before answering PDF-related questions.\n"
            "- Use `search_tool` for current events, recent information, or information "
            "that requires an internet search.\n"
            "- Use `calculator` for mathematical calculations. Do not calculate complex "
            "expressions manually when the calculator is available.\n"
            "- Use `get_stock_price` when the user asks for the current price of a stock.\n"
            "- Use `sell_stock` when the user wants to sell stocks.\n"
            "- Use `get_current_weather` when the user asks about current weather for a location.\n\n"

            "Answer general questions directly when no tool is required. "
            "Do not invent information from the uploaded document. "
            "If the user asks about a PDF but no document is available, ask them to upload a PDF. "
            "After receiving a tool result, provide a clear and helpful final answer."
        )
    )
    messages = [
        system_message,
        *state["messages"]
    ]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)  # Executes tool calls


conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
checkpoint = SqliteSaver(conn)



# graph structure
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)


graph.add_edge(START, "chat_node")

# If the LLM asked for a tool, go to ToolNode; else finish
graph.add_conditional_edges("chat_node", tools_condition)

graph.add_edge("tools", "chat_node")  

chatbot = graph.compile(checkpointer=checkpoint)



def get_all_threads():
    all_threads = set()
    for ckpt in checkpoint.list(None):
        all_threads.add(ckpt.config['configurable']['thread_id'])

    return list(all_threads)