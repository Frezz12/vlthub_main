from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.core.security import decode_token
from app.models.user import User
from app.schemas.dm import DirectMessageCreate, DirectMessageHistoryOut, DirectMessageOut, DirectMessageRoomOut, DirectMessageUpdate
from app.services import dm_service

CHAT_FILE_MAX_SIZE = dm_service.CHAT_FILE_MAX_SIZE

router = APIRouter(prefix="/direct", tags=["Direct Messages"])


class ReactionBody(BaseModel):
    emoji: str


@router.get("/rooms")
async def list_rooms(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[DirectMessageRoomOut]:
    rooms = await dm_service.get_user_rooms(session, user.id)
    result = []
    for r in rooms:
        out = await dm_service.room_to_out(r, user.id, session)
        result.append(out)
    return result


@router.post("/rooms/{other_user_id}")
async def get_or_create_room(
    other_user_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DirectMessageRoomOut:
    if other_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot chat with yourself")
    room = await dm_service.get_or_create_room(session, user.id, other_user_id)
    return await dm_service.room_to_out(room, user.id, session)


@router.post("/rooms/{room_id}/read", status_code=status.HTTP_200_OK)
async def mark_room_read(
    room_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    await dm_service.mark_room_read(session, room_id, user.id)
    return {"ok": True}


@router.get("/rooms/{room_id}/messages")
async def get_messages(
    room_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DirectMessageHistoryOut:
    messages, total = await dm_service.get_messages(session, room_id, user.id, limit, offset)
    return DirectMessageHistoryOut(
        messages=[dm_service.message_to_out(m, user.id) for m in messages],
        total=total,
    )


@router.post("/rooms/{room_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    room_id: str,
    body: DirectMessageCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DirectMessageOut:
    message = await dm_service.create_message(session, room_id, user.id, body.content, body.reply_to_id)
    out = dm_service.message_to_out(message, user.id)
    await _broadcast(room_id, out)
    return out


@router.post("/rooms/{room_id}/messages/with-file", status_code=status.HTTP_201_CREATED)
async def send_file_message(
    room_id: str,
    file: UploadFile = File(...),
    content: str = Form(default=""),
    reply_to_id: str = Form(default=""),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DirectMessageOut:
    data = await file.read()
    if len(data) > CHAT_FILE_MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 100 MB limit")
    rid = reply_to_id or None
    message = await dm_service.create_file_message(session, room_id, user.id, content, file.filename or "file", data, rid)
    out = dm_service.message_to_out(message, user.id)
    await _broadcast(room_id, out)
    return out


@router.patch("/rooms/{room_id}/messages/{message_id}")
async def edit_message(
    room_id: str,
    message_id: str,
    body: DirectMessageUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DirectMessageOut:
    message = await dm_service.update_message(session, message_id, user.id, body.content)
    out = dm_service.message_to_out(message, user.id)
    await _broadcast_edit(room_id, out)
    return out


@router.delete("/rooms/{room_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    room_id: str,
    message_id: str,
    scope: str = Query("all", pattern="^(all|self)$"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    await dm_service.delete_message(session, message_id, user.id, scope)
    await _broadcast_delete(room_id, message_id, scope, user.id)


@router.post("/rooms/{room_id}/messages/{message_id}/reactions", status_code=status.HTTP_200_OK)
async def toggle_reaction(
    room_id: str,
    message_id: str,
    body: ReactionBody,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DirectMessageOut:
    message = await dm_service.toggle_reaction(session, message_id, user.id, body.emoji)
    out = dm_service.message_to_out(message, user.id)
    await _broadcast_reaction(room_id, out)
    return out


@router.delete("/rooms/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: str,
    scope: str = Query("all", pattern="^(all|self)$"),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    await dm_service.delete_room(session, room_id, user.id, scope)
    await _broadcast_room_delete(room_id, scope, user.id)


# WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[tuple[WebSocket, str]]] = {}

    async def connect(self, room_id: str, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append((websocket, user_id))

    def disconnect(self, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                (ws, uid) for ws, uid in self.active_connections[room_id] if ws != websocket
            ]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket | None = None):
        if room_id not in self.active_connections:
            return
        for ws, _ in self.active_connections[room_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def _broadcast(room_id: str, out: DirectMessageOut) -> None:
    await manager.broadcast(room_id, out.model_dump(mode="json"))


async def _broadcast_edit(room_id: str, out: DirectMessageOut) -> None:
    payload = out.model_dump(mode="json")
    payload["_type"] = "edit"
    await manager.broadcast(room_id, payload)


async def _broadcast_room_delete(room_id: str, scope: str = "all", user_id: str | None = None) -> None:
    payload: dict = {"_type": "room_deleted", "room_id": room_id, "scope": scope}
    if user_id:
        payload["deleted_by"] = user_id
    await manager.broadcast(room_id, payload)


async def _broadcast_delete(room_id: str, message_id: str, scope: str = "all", user_id: str | None = None) -> None:
    payload: dict = {"_type": "delete", "id": message_id, "scope": scope}
    if user_id:
        payload["deleted_by"] = user_id
    await manager.broadcast(room_id, payload)


async def _broadcast_reaction(room_id: str, out: DirectMessageOut) -> None:
    payload = out.model_dump(mode="json")
    payload["_type"] = "reaction"
    await manager.broadcast(room_id, payload)


@router.websocket("/ws")
async def dm_websocket(
    websocket: WebSocket,
    room_id: str = Query(...),
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

    result.last_seen_at = datetime.now(timezone.utc)
    await session.commit()

    await manager.connect(room_id, websocket, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue
            message = await dm_service.create_message(session, room_id, user_id, content)
            out = dm_service.message_to_out(message, user_id)
            await manager.broadcast(room_id, out.model_dump(mode="json"))
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
