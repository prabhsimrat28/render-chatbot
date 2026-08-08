from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from backend import chatbot, get_all_threads, ingest_rag_document
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command
import uuid
import tempfile
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    thread_id: str
    message: str


class ResumeRequest(BaseModel):
    thread_id: str
    decision: str


def get_pending_interrupt(thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = chatbot.get_state(config)
        interrupts = getattr(state, "interrupts", ()) or ()
        if interrupts:
            return interrupts[0]
        tasks = getattr(state, "tasks", ()) or ()
        for task in tasks:
            task_interrupts = getattr(task, "interrupts", ()) or ()
            if task_interrupts:
                return task_interrupts[0]
    except Exception:
        return None
    return None


@app.get("/api/threads")
def list_threads():
    return {"threads": get_all_threads()}


@app.post("/api/threads")
def create_thread():
    return {"thread_id": str(uuid.uuid4())}


@app.get("/api/threads/{thread_id}/messages")
def get_messages(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = chatbot.get_state(config)
    messages = state.values.get("messages", [])
    result = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            result.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage) and msg.content:
            result.append({"role": "assistant", "content": msg.content})
    return {"messages": result}


@app.get("/api/threads/{thread_id}/interrupt")
def check_interrupt(thread_id: str):
    pending = get_pending_interrupt(thread_id)
    if pending:
        return {"pending": True, "prompt": str(pending.value)}
    return {"pending": False}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    config = {
        "configurable": {"thread_id": req.thread_id},
        "metadata": {"thread_id": req.thread_id},
        "run_name": "chat_trace",
    }

    async def generate():
        try:
            for chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=req.message)]},
                config=config,
                stream_mode="messages",
            ):
                if isinstance(chunk, ToolMessage):
                    tool_name = getattr(chunk, "name", "tool")
                    yield {"event": "tool_use", "data": json.dumps({"tool": tool_name})}
                if isinstance(chunk, AIMessage):
                    tccs = getattr(chunk, "tool_call_chunks", None)
                    if tccs:
                        for tc in tccs:
                            if tc.get("name"):
                                yield {"event": "tool_start", "data": json.dumps({"tool": tc["name"]})}
                    if chunk.content:
                        yield {"event": "token", "data": json.dumps({"content": chunk.content})}

            interrupt = get_pending_interrupt(req.thread_id)
            if interrupt:
                yield {"event": "interrupt", "data": json.dumps({"prompt": str(interrupt.value)})}

            yield {"event": "done", "data": "{}"}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(generate())


@app.post("/api/chat/resume")
async def resume_chat(req: ResumeRequest):
    config = {
        "configurable": {"thread_id": req.thread_id},
        "metadata": {"thread_id": req.thread_id},
        "run_name": "hitl_resume_trace",
    }

    async def generate():
        try:
            for chunk, metadata in chatbot.stream(
                Command(resume=req.decision),
                config=config,
                stream_mode="messages",
            ):
                if isinstance(chunk, ToolMessage):
                    tool_name = getattr(chunk, "name", "tool")
                    yield {"event": "tool_use", "data": json.dumps({"tool": tool_name})}
                if isinstance(chunk, AIMessage):
                    tccs = getattr(chunk, "tool_call_chunks", None)
                    if tccs:
                        for tc in tccs:
                            if tc.get("name"):
                                yield {"event": "tool_start", "data": json.dumps({"tool": tc["name"]})}
                    if chunk.content:
                        yield {"event": "token", "data": json.dumps({"content": chunk.content})}

            interrupt = get_pending_interrupt(req.thread_id)
            if interrupt:
                yield {"event": "interrupt", "data": json.dumps({"prompt": str(interrupt.value)})}

            yield {"event": "done", "data": "{}"}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(generate())


@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        ingest_rag_document(temp_path)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    from fastapi.staticfiles import StaticFiles

    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
