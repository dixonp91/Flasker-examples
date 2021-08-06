function randomColors() {
    return '#' + Math.floor(Math.random() * 16777215).toString(16);
  }


function myFunction() {
    document.getElementById("demo").style.color = randomColors();
  }