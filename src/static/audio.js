function toggleIcons(icon) {
    const listPlayIcons = document.querySelectorAll(".icon-play");
    const listPauseIcons = document.querySelectorAll(".icon-pause");
    var clickedIconPlay = icon.parentElement.querySelector(".icon-play");
    var clickedIconPause = icon.parentElement.querySelector(".icon-pause");

    // switch previous off
    const playIconsArray = Array.from(listPlayIcons); // Convert NodeList to array
    var currentSong = -1;

    // Get current playing song
    /*
    playIconsArray.forEach((item, index) => {
      if (item.classList.contains("d-none")) {
        currentSong =
        item.parentElement.parentElement.parentElement.id.split("-")[1];
        console.log("Current song", currentSong);
      }
    });
    */

    playIconsArray.forEach((item, index) => {
      //var pauseIcon = listPauseIcons[index];

      if (
        item.classList.contains("d-none") &&
        parseInt(item.id.split("-")[1]) !== parseInt(icon.id.split("-")[1])
      ) {
        item.classList.toggle("d-none");
        listPauseIcons[index].classList.toggle("d-none");
      }
    });

    // Switch clicked on
    clickedIconPlay.classList.toggle("d-none");
    clickedIconPause.classList.toggle("d-none");

    songName = clickedIconPlay.parentElement.parentElement
      .querySelector("div#songNameContainer")
      .querySelector("p").textContent;

    // Current song id
    currentSongId = parseInt(clickedIconPlay.id.split("-")[1]);

    getAudioSong(currentSongId, songName);

    // Toggle offcanvas on if not already
    getOffCanvas();
  }

  function getOffCanvas() {
    // Get reference to the offcanvas
    const offcanvas = new bootstrap.Offcanvas(
      document.getElementById("offcanvasScrolling")
    );

    // Toggle the offcanvas
    offcanvas.toggle();
  }

  function getAudioSong(songId, songName) {
    songContainer = document.getElementById("musicContainer");
    songLabel = document.getElementById("offcanvasBottomLabel");

    const songCard = `
      <div id="musicContainer">
        <audio controls autoplay style="width: 100%" id="audio">
          <source src="stream/${songId}" type="audio/mp3" />
        </audio>
      </div>
    `;

    songContainer.innerHTML = songCard;
    songLabel.textContent = songName;
  }