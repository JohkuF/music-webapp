from enum import Enum

class VoteType(Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"

class ChangeType(Enum):
    ON = "on"
    OFF = "off"
    
class AcceptedFileTypes(Enum):
    MP3 = "audio/mpeg"
    FLAC = "audio/flac"
    OGG = "audio/ogg"