function sanitize(string) {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#x27;",
      "/": "&#x2F;",
    };
    const reg = /[&<>"'/]/gi;
    return string.replace(reg, (match) => map[match]);
  }

  // Fetch messages
  async function fetchMessages() {
    var id = "{{ song_id }}";

    try {
      const response = await fetch(`/messages/${id}`);
      const messages = await response.json();

      var id_extra = 0;
      // Add messages to the containers
      const messagesContainer = document.getElementById(
        `messagesContainer-${id}`
      );

      messages.reverse().forEach((message) => {
        username = sanitize(message.username);
        content = sanitize(message.content);

        const messageCard = `
          <div class="card mb-4" id="messages-${id}-${id_extra}">
            <div class="card-body">
              <p>${content}</p>
              <div class="d-flex justify-content-between">
                <div class="d-flex flex-row align-items-center">
                  <p class="small mb-0 ms-2">${username}</p>
                </div>
              </div>
            </div>
          </div>`;
        id_extra++;
        messagesContainer.insertAdjacentHTML("beforeend", messageCard);
      });
    } catch (error) {
      console.error("Error fetching messages: ", error);
    }
  }