"""Tool schemas passed to the model, and the Pydantic model for each tool's
arguments.

Two things live here on purpose:

  TOOLS       - the JSON schemas sent to the model in the `tools` parameter
  ARG_MODELS  - the Pydantic model that validates what comes back

tool_guard.py validates every tool call against ARG_MODELS before the call is
allowed to run. Keeping both in one file makes it obvious that the thing we
advertise and the thing we validate are the same thing.
"""

import re

from pydantic import BaseModel, Field, field_validator

from app.tools.local_data import VALID_SERVICE_NAMES

# Source ticket IDs look like INC-ALP-0001: the family prefix, then a number.
TICKET_ID_PATTERN = re.compile(r"^INC-[A-Z]{3}-\d{4}$")


class LookupTicketArgs(BaseModel):
    """Arguments for lookup_ticket."""

    model_config = {"extra": "forbid"}

    ticket_id: str = Field(description="Ticket ID, e.g. INC-ALP-0001")

    @field_validator("ticket_id")
    @classmethod
    def must_look_like_a_ticket_id(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not TICKET_ID_PATTERN.match(cleaned):
            raise ValueError(
                "ticket_id must look like INC-ALP-0001 "
                "(INC, a three-letter family, four digits)"
            )
        return cleaned


class CheckServiceStatusArgs(BaseModel):
    """Arguments for check_service_status."""

    model_config = {"extra": "forbid"}

    # Checked against the service list loaded from services.json rather than a
    # hand-copied Literal, so the schema the model sees and the data the tool
    # reads can never drift apart.
    service_name: str = Field(description="Name of the internal service to check")

    @field_validator("service_name")
    @classmethod
    def must_be_a_known_service(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in VALID_SERVICE_NAMES:
            raise ValueError(
                f"unknown service {cleaned!r}. "
                f"Known services: {', '.join(VALID_SERVICE_NAMES)}"
            )
        return cleaned


class SearchKbArgs(BaseModel):
    """Arguments for search_kb."""

    model_config = {"extra": "forbid"}

    query: str = Field(min_length=3, max_length=300, description="Search terms")


ARG_MODELS: dict[str, type[BaseModel]] = {
    "lookup_ticket": LookupTicketArgs,
    "check_service_status": CheckServiceStatusArgs,
    "search_kb": SearchKbArgs,
}


# The schemas the model sees. Written out longhand rather than generated from
# the Pydantic models above, because this is the exact payload that goes over
# the wire and it gets read on screen.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_ticket",
            "description": (
                "Look up one past IT incident by its ticket ID and return its "
                "root cause and the steps that resolved it. Use this when the "
                "user quotes a ticket ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "Ticket ID, e.g. INC-ALP-0001",
                    }
                },
                "required": ["ticket_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_service_status",
            "description": (
                "Check whether an internal service is currently working. Use "
                "this when the user asks if something is up, down, or slow."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        # Same list the validator uses, from services.json.
                        "enum": VALID_SERVICE_NAMES,
                        "description": "Name of the internal service to check",
                    }
                },
                "required": ["service_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": (
                "Search the internal IT knowledge base for policy and how-to "
                "documents. Use this for questions about how to do something "
                "or what the policy is."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search terms",
                    }
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_NAMES = [tool["function"]["name"] for tool in TOOLS]
