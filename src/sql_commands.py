from sqlalchemy import text

SQL_FILE_UPLOAD = text(
    """
    with user_data AS (
    SELECT id FROM users WHERE username = (:username)
    )
    INSERT INTO uploads (
        user_id,
        upload_time,
        song_name,
        song_description,
        filepath,
        filename
        )
        VALUES (
        (SELECT id from user_data),
        NOW()::TIMESTAMP,
        (:songName),
        (:description),
        (:filepath),
        (:filename)
    );
"""
)
