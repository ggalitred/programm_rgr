const passedBtn = document.getElementById('show-passed');
const passedBlocks = document.querySelectorAll('.app_passed');

const waitedBtn = document.getElementById('show-waited');
const waitedBlocks = document.querySelectorAll('.app_waited');

const rejectedBtn = document.getElementById('show-rejected');
const rejectedBlocks = document.querySelectorAll('.app_rejected');


if(passedBlocks.length == 0) {
	passedBtn.style.backgroundColor = "grey";
}

if(waitedBlocks.length == 0) {
	waitedBtn.style.backgroundColor = "grey";
}

if(rejectedBlocks.length == 0) {
	rejectedBtn.style.backgroundColor = "grey";
}

passedBtn.addEventListener('click', () => {

  passedBlocks.forEach(block => {
    if (block.hidden == true){
		passedBtn.style.backgroundColor = "#4CAF50";
        block.hidden = false;
    } else {
		passedBtn.style.backgroundColor = "grey";
        block.hidden = true;
    }
    });
});

waitedBtn.addEventListener('click', () => {
	
  waitedBlocks.forEach(block => {
    if (block.hidden == true){
		waitedBtn.style.backgroundColor = "#FFC107";
        block.hidden = false;
    } else {
		waitedBtn.style.backgroundColor = "grey";
        block.hidden = true;
    }
    });
});

rejectedBtn.addEventListener('click', () => {

  rejectedBlocks.forEach(block => {
    if (block.hidden == true){
		rejectedBtn.style.backgroundColor = "#DC3545";
        block.hidden = false;
    } else {
		rejectedBtn.style.backgroundColor = "grey";
        block.hidden = true;
    }
    });
});