function toggleVote(icon) {
    var otherId = icon.id
    if (otherId.split("-")[1] === "on") {
        otherId = otherId.replace("on", "off");
    } else {
        otherId = otherId.replace("off", "on");
    }

    var other = icon.parentElement.querySelector("#"+otherId);
    var clickedClass = icon.getAttribute("class");
    var otherClass = other.getAttribute("class");
    
    clickedClass += " d-none"
    other.classList.remove("d-none")
    icon.setAttribute("class", clickedClass.trim());


    // Check if 

    /*
    // Update otherId based on the state of the clicked icon
    
    
    if (clickedClass.includes("d-none")) {
        // If "d-none" is present, remove it
        clickedClass = clickedClass.replace("d-none", "");
        
    } else {
        // If "d-none" is not present, add it
        clickedClass += " d-none";
    }
    
    if (otherClass.includes("d-none")) {
        // If "d-none" is present, remove it
        otherClass = otherClass.replace("d-none", "");
    } else {
        // If "d-none" is not present, add it
        otherClass += " d-none";
    }
    
    */
}