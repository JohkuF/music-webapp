# music-webapp
![Screen Shot 2024-09-19 at 20 51 36](https://github.com/user-attachments/assets/12a96588-7b8a-41b6-9af1-05f8a3f3ae41)

## Music Streaming Platform for HY-TSOHA Course
### Tutorial
* Upon starting the platform, the first user created is automatically assigned the admin role.
  > The admin has access to the settings panel, where they can enable or disable user signups and song uploads.
* Upload songs via the Upload tab.
  > Songs can be marked as either Private or Public. Featured songs are displayed on the Home page, all uploaded songs can be found under Explore, and your personal uploads are located in Library.
* Users can listen to, like, and comment on any public song.
### Cool Features
* Dynamic Commenting
  > Comments can be added in real-time without needing to refresh the page, ensuring uninterrupted playback.
* Auto Play
  > The next song automatically plays when the current one ends. This feature is currently supported on PC and some Android devices.
 * Fast and responsive voting system.
 * Basic song statistics.
 * User settings.


## STARTUP

### Required .env file
```.env
SECRET_KEY=TEMP
POSTGRES_PASSWORD=TEMP
POSTGRES_SUPERUSER_PASSWORD=TEMP
POSTGRES_USER=musicApp
POSTGRES_VOLUME=pgdata2
UPLOAD_FOLDER=/data/
```
then: 
`docker compose up --build`

### Or setup dev-environment (NOTE: File upload does not work)
```
poetry install
poetry run python3 -m src
```
