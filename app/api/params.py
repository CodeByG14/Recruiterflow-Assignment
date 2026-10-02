"""Shared path-parameter types."""

from typing import Annotated

from fastapi import Path

# Identity columns are 32-bit positive integers. Anything else is a 422,
# never a database round trip.
MAX_ID = 2_147_483_647

IdPath = Annotated[int, Path(ge=1, le=MAX_ID, description="Numeric record id")]
