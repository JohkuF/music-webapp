from sqlalchemy import text

# TODO maybe songs_id_seq could go out of sync - maybe use id from first insert
SQL_FILE_UPLOAD = text(
    """WITH user_data AS (
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
            0;"""
)


SQL_SEND_MESSAGE_GENERAL = text(
    """
    WITH user_data AS (
        SELECT id FROM users WHERE username = :username
    )
    
    INSERT INTO messages (
        user_id,
        upload_time,
        content
    )
    VALUES (
        (SELECT id FROM user_data),
        NOW(),
        :content
    )
"""
)

SQL_FETCH_MESSAGES_GENERAL = text(
    """SELECT users.username, messages.content
       FROM messages
       JOIN users ON messages.user_id = users.id;"""
)


SQL_FETCH_MESSAGES_ON_SONG = text(
    """SELECT users.username, messages.song_id, messages.content
       FROM messages
       JOIN users ON messages.user_id = users.id
       WHERE (:song_id IS NULL OR messages.song_id = :song_id);"""
)

SQL_UPDATE_SONG_UPVOTE = text(
    """UPDATE song_metadata 
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
