from enum import Enum
from pydantic import BaseModel

from .myenums import VoteType, ChangeType


class VoteSchema(BaseModel):
    id: int
    type: VoteType
