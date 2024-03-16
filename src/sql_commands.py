from sqlalchemy import text

SQL_FILE_UPLOAD = text(
    """
    INSERT INTO songs (
        song_name,
        song_description
    )
    VALUES (
        :song_name,
        :song_description
    );
    
    WITH user_data AS (
        SELECT id FROM users WHERE username = :username
    )

    INSERT INTO uploads (
        user_id,
        song_id,
        upload_time,
        filepath,
        filename
    )
    VALUES (
        (SELECT id FROM user_data),
        currval('songs_id_seq'),
        NOW(),
        :filepath,
        :filename
    );
"""
)
