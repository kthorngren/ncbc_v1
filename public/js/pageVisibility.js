// variable to record if video has been paused
// video is set to autoplay so initially is not paused 
sessionStorage.isPaused = "false";

// set name of hidden property and visibility change event
var hidden, visibilityChange; 
if (typeof document.hidden !== "undefined") {
	hidden = "hidden";
	visibilityChange = "visibilitychange";
} else if (typeof document.mozHidden !== "undefined") {
	hidden = "mozHidden";
	visibilityChange = "mozvisibilitychange";
} else if (typeof document.msHidden !== "undefined") {
	hidden = "msHidden";
	visibilityChange = "msvisibilitychange";
} else if (typeof document.webkitHidden !== "undefined") {
	hidden = "webkitHidden";
	visibilityChange = "webkitvisibilitychange";
}
 

// if the page is hidden, pause the video
// if the page is shown, play the video
function handleVisibilityChange() {
	if (document[hidden]) {
		console.log(Date() + ': hidden');
	} else if (sessionStorage.isPaused !== "true") {
		sessionStorage.isPaused = "false";
		display_date();
	}
}



// warn if the browser doesn't support addEventListener or the Page Visibility API
if (typeof document.addEventListener === "undefined" || 
	typeof hidden === "undefined") {
	alert("This demo requires a browser such as Google Chrome that supports the Page Visibility API.");
} else {

    // handle page visibility change
    // see https://developer.mozilla.org/en/API/PageVisibility/Page_Visibility_API
    document.addEventListener(visibilityChange, handleVisibilityChange, false);
}
    

function display_date() {
	//console.log(Date());
	if (!document[hidden]) {
        setTimeout(display_date, 1000);
    }
}


display_date();