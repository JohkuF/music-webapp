from enum import Enum
from pydantic import BaseModel

from .myenums import VoteType


class VoteSchema(BaseModel):
    id: int
    type: VoteType
