# Agentic Chatbot

A Streamlit chatbot built with LangGraph, LangChain, Groq, and several external tools. The application supports normal conversations, web search, calculations, stock and weather queries, PDF based question answering, and human approval for stock purchase and sale actions.

## Key Features

- **Chat with an LLM**
  - Uses `gpt-oss-20b` through the Groq API.
  - The model can decide whether to answer directly or use one of the available tools.

- **Multiple tools**
  - Web search using Tavily.
  - Mathematical calculations using a calculator tool.
  - Current stock prices using Alpha Vantage.
  - Current weather using OpenWeatherMap.
  - PDF question answering using a FAISS vector database.
  - Mock stock purchase and sale tools with human approval.

- **PDF based question answering**
  - Upload a PDF directly through the Streamlit chat input.
  - The PDF is loaded using `PyPDFLoader`.
  - Text is split into smaller chunks using `RecursiveCharacterTextSplitter`.
  - Chunks are converted into embeddings using a custom `JinaEmbeddings` class.
  - The embeddings are stored in a local FAISS database.
  - Relevant chunks are retrieved when the user asks a question about the PDF.

- **Human approval for stock actions**
  - Stock purchases and sales do not happen immediately.
  - The LangGraph `interrupt()` function pauses execution and waits for the user.
  - The Streamlit interface shows Approve and Reject buttons.
  - The graph resumes using `Command(resume=decision)`.

- **Multiple conversations**
  - Each conversation gets its own thread ID.
  - Previous conversations can be selected from the sidebar.
  - LangGraph's SQLite checkpointer stores the conversation state.

## How Threads Work

Each chat conversation is assigned a unique UUID.

For example:

```text
550e8400-e29b-41d4-a716-446655440000
```

This ID is passed to LangGraph through the configuration:

```python
config = {
    "configurable": {
        "thread_id": thread_id
    }
}
```

LangGraph uses the thread ID to keep different conversations separate.

The application stores the checkpoints in:

```text
chatbot.db
```

When the user switches to an older conversation, the application uses its thread ID to retrieve the saved state from LangGraph.

The sidebar therefore works like a conversation history. Each entry represents a different LangGraph thread.

## How Streamlit Session State Is Used

Streamlit reruns the Python script whenever the user interacts with the application. Because of this, temporary UI information needs to be stored in `st.session_state`.

This project uses session state for several things.

### Message History

```python
st.session_state["message_history"]
```

Stores the messages currently displayed in the Streamlit interface.

It contains dictionaries such as:

```python
{
    "role": "user",
    "content": "What is the weather today?"
}
```

and:

```python
{
    "role": "assistant",
    "content": "..."
}
```

This is mainly used for displaying the current conversation in the UI. The actual persistent conversation state is handled by LangGraph's SQLite checkpointer.

### Current Thread ID

```python
st.session_state["thread_id"]
```

Stores the thread ID of the conversation currently selected by the user.

When a new chat is created, a new UUID is generated.

### Chat Threads

```python
st.session_state["chat_threads"]
```

Stores the thread IDs shown in the sidebar.

The application also gets existing thread IDs from the LangGraph SQLite checkpointer when the application starts.

### Pending Human Approval

```python
st.session_state["pending_hitl"]
```

Stores information about a pending stock purchase or sale approval.

It contains the thread ID and the message that should be displayed to the user.

This allows the approval request to remain visible after a Streamlit rerun or page refresh.

## Human in the Loop

The stock purchase and sale tools use LangGraph's `interrupt()` function.

For example:

```python
decision = interrupt(
    f"Approve buying {quantity} shares of {symbol}?"
)
```

At this point, graph execution pauses.

The Streamlit application detects the pending interrupt and displays:

- Approve Purchase
- Reject Purchase

When the user selects an option, the graph is resumed:

```python
chatbot.stream(
    Command(resume=decision),
    config=resume_config,
    stream_mode="messages"
)
```

The decision is then received by the interrupted tool.

`yes` completes the mock transaction, while another response rejects it.

## RAG Pipeline

The PDF workflow follows these steps:

```text
PDF Upload
    ↓
PyPDFLoader
    ↓
Text Splitting
    ↓
Jina Embeddings
    ↓
FAISS Vector Store
    ↓
Similarity Search
    ↓
Relevant PDF Chunks
    ↓
LLM Answer
```

### PDF Loading

`PyPDFLoader` reads the uploaded PDF.

### Text Splitting

`RecursiveCharacterTextSplitter` creates chunks using:

- Chunk size: 1000
- Chunk overlap: 200

### Embeddings

The project uses a custom `JinaEmbeddings` implementation to create vector representations of the document chunks and user queries.

### Vector Store

FAISS stores the generated vectors locally in:

```text
faiss_db
```

The retriever uses similarity search and returns the top 4 relevant chunks.

## APIs and Models Used

### Groq

The LLM is accessed through the OpenAI compatible API provided by Groq.

Model:

```text
openai/gpt-oss-120b
```

The application uses:

```text
GROQ_API_KEY
```

as the API key.

### Jina

Jina is used for document and query embeddings through the project's custom `JinaEmbeddings` class.

The application uses:

```text
JINA_API_KEY
```

as the API key.

### Tavily

Tavily provides the web search tool used by the chatbot for current or internet based information.

The application uses the Tavily search tool with:

- Maximum results: 5
- Topic: general
- Search depth: advanced

### Alpha Vantage

Alpha Vantage is used to retrieve stock prices.

The application uses the `GLOBAL_QUOTE` endpoint and requires:

```text
VANTAGE_API_KEY
```

### OpenWeatherMap

OpenWeatherMap is used by the weather tool to retrieve current weather information for a location.

The application uses:

```text
WEATHER_API_KEY
```

## Main Technologies

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web interface |
| LangGraph | Conversation flow, tools, threads, and interrupts |
| LangChain | LLM and tool integration |
| Groq | LLM API |
| Jina | Embeddings |
| FAISS | Vector similarity search |
| Tavily | Web search |
| Alpha Vantage | Stock prices |
| OpenWeatherMap | Weather data |
| SQLite | LangGraph checkpoint storage |
| Docker | Containerization |

## Project Structure

```text
project/
│
├── app.py
├── backend.py
├── JinaEmbeddings.py
├── requirements.txt
├── Dockerfile
├── .streamlit/
│   └── config.toml
│
├── faiss_db/
└── chatbot.db
```

`faiss_db` and `chatbot.db` are created/used at runtime.

## Environment Variables

Create a `.env` file when running the project locally:

```env
GROQ_API_KEY=your_groq_api_key
JINA_API_KEY=your_jina_api_key
TAVILY_API_KEY=your_tavily_api_key
VANTAGE_API_KEY=your_alpha_vantage_api_key
WEATHER_API_KEY=your_openweathermap_api_key
```

Do not commit `.env` to GitHub.

For deployment, add these values as environment variables in the hosting platform.

## Running Locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Then start the Streamlit application:

```bash
streamlit run app.py
```

The application will open in your browser.

## Docker

The project also includes a Dockerfile for running the application inside a container.

Build the image:

```bash
docker build -t agentic-chatbot .
```

Run it:

```bash
docker run -p 10000:10000 agentic-chatbot
```

## Notes

- The stock purchase and sale functions are mock functions. They do not perform real stock transactions.
- API keys should be kept in environment variables and should never be committed to GitHub.
- The FAISS database and SQLite checkpoint database are local files used by the application.
