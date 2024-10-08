-- Drop the existing app database if it exists
--DROP DATABASE IF EXISTS app;

-- Drop the existing roles if they exist
--DROP ROLE IF EXISTS app_user;
--DROP ROLE IF EXISTS postgres;


CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '${POSTGRES_SUPERUSER_PASSWORD}';

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
    song_description TEXT,
    is_public BOOLEAN
);

CREATE TABLE song_metadata (
    song_id INT REFERENCES songs(id), 
    comments INT,
    plays INT,
    upvote INT,
    downvote INT,
    nonevote INT,
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

CREATE TABLE states (
    id SERIAL PRIMARY KEY,
    state_name TEXT,
    allow_signup BOOLEAN
);

INSERT INTO states (state_name, allow_signup) VALUES ('signup', true), ('upload', true);

INSERT INTO signup_state (allow_signup) VALUES (true);

--GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
--GRANT ALL PRIVILEGES ON SEQUENCE users_id_seq, songs_id_seq, uploads_id_seq, messages_id_seq TO app_user;
