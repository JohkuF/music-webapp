from sqlalchemy import text

# TODO maybe songs_id_seq could go out of sync - maybe use id from first insert
SQL_FILE_UPLOAD = text(
    """
WITH user_data AS (
        SELECT id FROM users WHERE username = :username
    ),
    insert_song AS (
        INSERT INTO songs (
            song_name,
            song_description,
            is_public
        )
        VALUES (
            :song_name,
            :song_description,
            :is_public
        )
        RETURNING id
    ),
    insert_upload AS (
        INSERT INTO uploads (
            user_id,
            song_id,
            upload_time,
            filepath,
            filename
        )
        SELECT 
            (SELECT id FROM user_data),
            (SELECT id FROM insert_song),
            NOW(),
            :filepath,
            :filename
        RETURNING song_id
    )
    INSERT INTO song_metadata (
        song_id,
        playlists,
        comments,
        plays,
        upvote,
        downvote
    )
    SELECT 
        (SELECT song_id FROM insert_upload),
        0,
        0,
        0,
        0,
        0;
"""
)

SQL_FETCH_MESSAGES_GENERAL = text(
    """
SELECT users.username, messages.content
FROM messages
JOIN users ON messages.user_id = users.id;"""
)


SQL_FETCH_MESSAGES_ON_SONG = text(
    """
SELECT users.username, messages.song_id, messages.content, messages.upload_time
FROM messages
JOIN users ON messages.user_id = users.id
WHERE (:song_id IS NULL OR messages.song_id = :song_id);
"""
)

SQL_UPDATE_SONG_UPVOTE = text(
    """
UPDATE song_metadata 
SET upvote = upvote + 1
WHERE song_id = :song_id;
"""
)

SQL_INSERT_VOTE = text(
    """
WITH user_data AS (
    SELECT id FROM users WHERE username = :username
)
INSERT INTO likes (
    user_id,
    target_id,
    target_type,
    vote_type
)
SELECT
    (SELECT id FROM user_data),
    :target_id,
    :target_type,
    :vote_tfield, field2ype;
"""
)


SQL_DELETE_SONG = text(
    """
UPDATE songs
SET song_name = '[deleted]', song_description = '[deleted]'
WHERE id = :song_id AND id IN (
    SELECT song_id
    FROM uploads
    WHERE user_id = :user_id
);
"""
)

SQL_UPDATE_PASSWORD = text(
    """
UPDATE users
SET password=:hashed_password
WHERE username=:username AND id=:user_id;
"""
)

SQL_DELETE_ACCOUNT = text(
    """
UPDATE users
SET username = '[deleted]',
    password = '[deleted]'
WHERE username = :username AND id = :user_id;
"""
)

SQL_CHANGE_PUBLICITY = text(
    """
UPDATE songs s
SET is_public = :is_public
FROM uploads u
WHERE (s.id = :song_id) AND 
      (s.id = u.song_id) AND 
      (u.user_id = :user_id);
"""
)

SQL_LOGIN = text("SELECT id, password FROM users WHERE username=:username")

SQL_USER_COUNT = text("SELECT COUNT(*) AS row_count FROM users;")

SQL_CHECK_USERNAME_EXISTS = text(
    "SELECT id, password FROM users WHERE username=:username"
)

SQL_CREATE_NEW_USER = text(
    "INSERT INTO users (username, password, role) VALUES (:username, :password, :role)"
)

SQL_GET_SONG_FILEPATH = text(
    """
SELECT filepath, filename FROM uploads
WHERE song_id = :song_id;
"""
)

SQL_UPDATE_SONG_METADATA = text(
    """
UPDATE song_metadata
SET plays = plays + 1
WHERE song_id = :song_id
"""
)

# ---------- DYNAMIC MESSAGE ----------
# Has dynamic changes later on. No text()

SQL_GET_SONGS_DEFAULT = """
SELECT songs.*, song_metadata.*, u.user_id
FROM songs
LEFT JOIN song_metadata ON songs.id = song_metadata.song_id
LEFT JOIN uploads u ON u.song_id = songs.id
WHERE (:user_id IS NULL OR u.user_id = :user_id)
AND (:is_public IS NULL OR songs.is_public = :is_public)
AND (songs.song_name <> '[deleted]')
ORDER BY (song_metadata.upvote - song_metadata.downvote) DESC
"""

SQL_SEND_MESSAGE = text(
    """
INSERT INTO messages (song_id, user_id, upload_time, content)
SELECT :song_id, id, NOW(), :content FROM users WHERE username = :username;

UPDATE song_metadata
SET comments = comments + 1 
WHERE song_id = :song_id;
"""
)

# ---------- VOTE PROCESSING ----------

SQL_VOTE_INSERT_NEW_VOTE = """
-- Insert to likes
INSERT INTO likes (user_id, target_id, target_type, vote_type)
VALUES (:user_id, :target_id, :target_type, :vote_type);
"""

SQL_VOTE_UPDATE_EXISTING_VOTE = """
-- Update likes
UPDATE likes
SET vote_type = :vote_type
WHERE user_id = :user_id AND target_id = :target_id AND target_type = 'song';

-- Adjust song_metadata for the old vote
UPDATE song_metadata
SET {prev_vote_type} = {prev_vote_type} - 1
WHERE song_id = :target_id;
"""

SQL_VOTE_UPDATE_SONG_METADATA = """
-- Update song_metadata with the new vote
UPDATE song_metadata
SET {vote_type} = {vote_type} + 1
WHERE song_id = :target_id;
"""
