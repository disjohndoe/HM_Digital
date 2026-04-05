from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.agent_connection_manager import agent_manager


async def verify_card_matches_doctor(
    tenant_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> tuple[bool, str]:
    """Check if any connected agent has the given doctor's card inserted."""
    user = await db.get(User, user_id)
    if not user:
        return False, "Korisnik nije pronađen"

    if not user.card_holder_name:
        return False, "Doktor nema povezanu karticu"

    if not agent_manager.is_connected(tenant_id):
        return False, "Agent nije spojen"

    conn = agent_manager.find_by_card_holder(tenant_id, user.card_holder_name)
    if not conn:
        return False, "Kartica ovog doktora nije umetnuta ni u jednom agentu"

    return True, "OK"


def get_card_status(tenant_id: UUID, card_holder_name: str | None = None) -> dict:
    """Get card/agent status for a tenant, optionally scoped to a specific doctor."""
    any_connected = agent_manager.is_connected(tenant_id)
    agents_count = agent_manager.count(tenant_id)

    # Check if any agent has VPN connected
    vpn_connected = any(c.vpn_connected for c in agent_manager.get_all(tenant_id))

    # Find the agent with this doctor's card
    my_card_inserted = False
    card_holder = None
    if card_holder_name:
        conn = agent_manager.find_by_card_holder(tenant_id, card_holder_name)
        if conn:
            my_card_inserted = True
            card_holder = conn.card_holder

    return {
        "agent_connected": any_connected,
        "agents_count": agents_count,
        "card_inserted": my_card_inserted,
        "card_holder": card_holder,
        "vpn_connected": vpn_connected,
    }
