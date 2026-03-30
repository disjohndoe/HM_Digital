import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service, auth_service
from app.services.agent_connection_manager import agent_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket):
    # Extract auth params from query string
    tenant_id_str = websocket.query_params.get("tenant_id")
    agent_secret = websocket.query_params.get("agent_secret")

    if not tenant_id_str or not agent_secret:
        await websocket.close(code=4001, reason="Missing tenant_id or agent_secret")
        return

    try:
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid tenant_id format")
        return

    # Verify secret against DB
    async with async_session() as db:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant or tenant.agent_secret != agent_secret:
            await websocket.close(code=4003, reason="Invalid credentials")
            return

    # Accept and register
    await agent_manager.connect(tenant_id, websocket)
    await websocket.send_json({"type": "connected", "message": "Agent spojen"})

    # Start ping loop
    ping_task = asyncio.create_task(_ping_loop(tenant_id))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "pong":
                agent_manager.update_heartbeat(tenant_id)

            elif msg_type == "status":
                # Capture previous card state before update
                conn = agent_manager.get(tenant_id)
                was_inserted = conn.card_inserted if conn else False

                agent_manager.update_status(
                    tenant_id,
                    card_inserted=msg.get("card_inserted"),
                    vpn_connected=msg.get("vpn_connected"),
                    card_holder=msg.get("card_holder"),
                )

                # Card removal detection: revoke sessions for card-required users
                now_inserted = msg.get("card_inserted", was_inserted)
                if was_inserted and not now_inserted:
                    await _handle_card_removal(tenant_id)

            elif msg_type in ("sign_response", "sign_error"):
                # Future: forward to waiting request
                logger.info("Received %s from agent for tenant %s", msg_type, tenant_id)

    except WebSocketDisconnect:
        logger.info("Agent WebSocket disconnected for tenant %s", tenant_id)
    except Exception:
        logger.exception("Agent WebSocket error for tenant %s", tenant_id)
    finally:
        ping_task.cancel()
        await agent_manager.disconnect(tenant_id)


async def _ping_loop(tenant_id):
    """Send ping every 30s to keep connection alive."""
    try:
        while True:
            await asyncio.sleep(30)
            sent = await agent_manager.send_to_agent(tenant_id, {"type": "ping"})
            if not sent:
                break
    except asyncio.CancelledError:
        pass


async def _handle_card_removal(tenant_id: UUID) -> None:
    """Revoke sessions for all card-required users when smart card is removed."""
    logger.warning("Card removal detected for tenant %s — revoking card-required sessions", tenant_id)

    async with async_session() as db:
        async with db.begin():
            # Find all card-required users in this tenant
            result = await db.execute(
                select(User).where(
                    User.tenant_id == tenant_id,
                    User.card_required.is_(True),
                    User.is_active.is_(True),
                )
            )
            users = result.scalars().all()

            for user in users:
                count = await auth_service.revoke_user_sessions(db, tenant_id, user.id)
                if count > 0:
                    logger.info(
                        "Revoked %d session(s) for user %s (card removal)", count, user.email
                    )
                    await audit_service.write_audit(
                        db,
                        tenant_id=tenant_id,
                        user_id=user.id,
                        action="card_removal_session_revoked",
                        resource_type="session",
                        details={"sessions_revoked": count},
                    )
