from sqlalchemy import text

# TODO maybe songs_id_seq could go out of sync - maybe use id from first insert
SQL_FILE_UPLOAD = text(
    """WITH user_data AS (
            SELECT id FROM users WHERE username = :username
        ),
        insert_song AS (
            INSERT INTO songs (
                song_name,
                song_description
            )
            VALUES (
                :song_name,
                :song_description
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
    """SELECT users.username, messages.content
       FROM messages
       JOIN users ON messages.user_id = users.id
       WHERE messages.song_id = :song_id;"""
)
