-- Drop the existing app database if it exists
--DROP DATABASE IF EXISTS app;

-- Drop the existing roles if they exist
--DROP ROLE IF EXISTS app_user;
--DROP ROLE IF EXISTS postgres;


CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'TEMPPASS';

--CREATE ROLE app_user WITH LOGIN PASSWORD 'TEMPPASS';
--GRANT ALL PRIVILEGES ON DATABASE app TO app_user;

--CREATE DATABASE app;

-- Connect to the app database
\c musicApp;


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    role TEXT
);

--CREATE TABLE users_metadata (
--    id SERIAL PRIMARY KEY, 
--    user_id INT REFERENCES users(id),
--    songs_listened INT,
--)

CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    song_name TEXT,
    song_description TEXT
);

CREATE TABLE song_metadata (
    song_id INT REFERENCES songs(id), 
    playlists INT,
    comments INT,
    plays INT,
    upvote INT,
    downvote INT,
    PRIMARY KEY (song_id)
);

-- TODO: Change (song_id) to (target_id) so more flexible commenting
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    song_id INT REFERENCES songs(id),
    user_id INT REFERENCES users(id),
    upload_time TIMESTAMP,
    content TEXT
);

CREATE TABLE playlists (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    playlist_name TEXT,
    created_at TIMESTAMP
);

CREATE TABLE playlist_song (
    playlist_id INT REFERENCES playlists(id),
    song_id INT REFERENCES songs(id),
    PRIMARY KEY (playlist_id, song_id)
);

CREATE TABLE likes (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    target_id INT,
    target_type TEXT,
    vote_type TEXT
);

CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    song_id INT REFERENCES songs(id),
    upload_time TIMESTAMP,
    filepath TEXT,
    filename TEXT
);

CREATE TABLE signup_state (
    id SERIAL PRIMARY KEY,
    allow_signup BOOLEAN
);

INSERT INTO signup_state (allow_signup) VALUES (true);

--GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
--GRANT ALL PRIVILEGES ON SEQUENCE users_id_seq, songs_id_seq, uploads_id_seq, messages_id_seq TO app_user;
