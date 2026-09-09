"""What each tool actually does.

Every handler reads the committed local data and nothing else. No network
call, no external service -- so a tool call cannot fail because the venue
wifi did, and every answer is checkable by anyone in the room.

Handlers assume their arguments are already validated. tool_guard.py does
that, and nothing should call a handler without going through it.
"""

from app.agents.retriever import search
from app.tools.local_data import SERVICES, TICKETS, VALID_SERVICE_NAMES


def lookup_ticket(ticket_id: str) -> dict:
    """Return one past incident's root cause and how it was resolved."""
    ticket = TICKETS.get(ticket_id)
    if ticket is None:
        return {
            "found": False,
            "message": f"No incident on record with ID {ticket_id}.",
        }
    return {"found": True, **ticket}


def check_service_status(service_name: str) -> dict:
    """Return the current state of one internal service."""
    service = SERVICES.get(service_name)
    if service is None:
        return {
            "found": False,
            "message": (
                f"No service called {service_name}. "
                f"Known services: {', '.join(VALID_SERVICE_NAMES)}."
            ),
        }
    return {"found": True, **service}


def search_kb(query: str) -> dict:
    """Search the knowledge base. Returns titles and text, not raw vectors."""
    documents = search(query)
    return {
        "found": bool(documents),
        "documents": [
            {"source": d["source"], "title": d["title"], "text": d["text"]}
            for d in documents
        ],
    }


HANDLERS = {
    "lookup_ticket": lookup_ticket,
    "check_service_status": check_service_status,
    "search_kb": search_kb,
}
