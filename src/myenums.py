from enum import Enum

class VoteType(Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    NONEVOTE = "nonevote"

# TODO: add target type to add possibility to like comments

    
class AcceptedFileTypes(Enum):
    MP3 = "audio/mpeg"
    FLAC = "audio/flac"
    OGG = "audio/ogg"