from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_project_or_404, require_chat_enabled
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.security import decode_token
from app.models.project import Project
from app.models.user import User
from sqlalchemy import select
from app.schemas.chat import ChatHistoryOut, ChatMessageCreate, ChatMessageOut, ChatMessageUpdate, ChatVersionAttach
from app.services import chat_service

CHAT_FILE_MAX_SIZE = chat_service.CHAT_FILE_MAX_SIZE

router = APIRouter(prefix="/projects/{project_id}/chat", tags=["Chat"])


class ReactionBody(BaseModel):
    emoji: str


@router.get("")
async def get_chat_messages(
    project_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
) -> ChatHistoryOut:
    messages, total = await chat_service.get_messages(session, project_id, user.id, limit, offset)
    return ChatHistoryOut(
        messages=[chat_service.message_to_out(m) for m in messages],
        total=total,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def send_message(
    project_id: str,
    body: ChatMessageCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
) -> ChatMessageOut:
    message = await chat_service.create_message(session, project_id, user.id, body.content, body.reply_to_id)
    out = chat_service.message_to_out(message)
    await _broadcast(project_id, out)
    return out


@router.post("/with-file", status_code=status.HTTP_201_CREATED)
async def send_file_message(
    project_id: str,
    file: UploadFile = File(...),
    content: str = Form(default=""),
    reply_to_id: str = Form(default=""),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
) -> ChatMessageOut:
    data = await file.read()
    if len(data) > CHAT_FILE_MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 100 MB limit")
    rid = reply_to_id or None
    message = await chat_service.create_file_message(session, project_id, user.id, content, file.filename or "file", data, rid)
    out = chat_service.message_to_out(message)
    await _broadcast(project_id, out)
    return out


@router.post("/with-version", status_code=status.HTTP_201_CREATED)
async def send_version_message(
    project_id: str,
    body: ChatVersionAttach,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
) -> ChatMessageOut:
    message = await chat_service.create_version_message(session, project_id, user.id, body.content, body.version_id, body.reply_to_id)
    out = chat_service.message_to_out(message)
    await _broadcast(project_id, out)
    return out


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    project_id: str,
    message_id: str,
    scope: str = Query("all", pattern="^(all|self)$"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
):
    await chat_service.delete_message(session, message_id, user.id, scope)
    await _broadcast_delete(project_id, message_id, scope, user.id)


@router.patch("/{message_id}")
async def edit_message(
    project_id: str,
    message_id: str,
    body: ChatMessageUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
) -> ChatMessageOut:
    message = await chat_service.update_message(session, message_id, user.id, body.content)
    out = chat_service.message_to_out(message)
    await _broadcast_edit(project_id, out)
    return out


@router.post("/{message_id}/reactions", status_code=status.HTTP_200_OK)
async def toggle_reaction(
    project_id: str,
    message_id: str,
    body: ReactionBody,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _: Project = Depends(get_project_or_404),
    _chat: None = Depends(require_chat_enabled),
) -> ChatMessageOut:
    message = await chat_service.toggle_reaction(session, message_id, user.id, body.emoji)
    out = chat_service.message_to_out(message)
    await _broadcast_reaction(project_id, out)
    return out


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[tuple[WebSocket, str]]] = {}

    async def connect(self, project_id: str, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append((websocket, user_id))

    def disconnect(self, project_id: str, websocket: WebSocket):
        if project_id in self.active_connections:
            self.active_connections[project_id] = [
                (ws, uid) for ws, uid in self.active_connections[project_id] if ws != websocket
            ]
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def broadcast(self, project_id: str, message: dict, exclude: WebSocket | None = None):
        if project_id not in self.active_connections:
            return
        for ws, _ in self.active_connections[project_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def _broadcast(project_id: str, out: ChatMessageOut) -> None:
    await manager.broadcast(project_id, out.model_dump(mode="json"))


async def _broadcast_edit(project_id: str, out: ChatMessageOut) -> None:
    payload = out.model_dump(mode="json")
    payload["_type"] = "edit"
    await manager.broadcast(project_id, payload)


async def _broadcast_delete(project_id: str, message_id: str, scope: str = "all", user_id: str | None = None) -> None:
    payload: dict = {"_type": "delete", "id": message_id, "scope": scope}
    if user_id:
        payload["deleted_by"] = user_id
    await manager.broadcast(project_id, payload)


async def _broadcast_reaction(project_id: str, out: ChatMessageOut) -> None:
    payload = out.model_dump(mode="json")
    payload["_type"] = "reaction"
    await manager.broadcast(project_id, payload)


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    project_id: str,
    token: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    result = await session.get(User, user_id)
    if not result:
        await websocket.close(code=4001)
        return

    proj = await session.execute(select(Project).where(Project.id == project_id))
    project = proj.scalar_one_or_none()
    if not project or not project.chat_enabled:
        await websocket.close(code=4003, reason="Chat is not enabled for this project")
        return

    await manager.connect(project_id, websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue
            message = await chat_service.create_message(session, project_id, user_id, content)
            out = chat_service.message_to_out(message)
            await manager.broadcast(project_id, out.model_dump(mode="json"))
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
