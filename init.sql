CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD 'TEMPPASS';

CREATE ROLE app_user WITH LOGIN PASSWORD 'TEMPPASS';
GRANT ALL PRIVILEGES ON DATABASE app TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON SEQUENCE users_id_seq, songs_id_seq, uploads_id_seq TO app_user;


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
    password TEXT,
    role TEXT
);

CREATE TABLE songs (
    id SERIAL PRIMARY KEY,
    song_name TEXT,
    song_description TEXT
);

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
