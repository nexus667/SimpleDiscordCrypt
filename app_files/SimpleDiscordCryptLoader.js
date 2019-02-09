const localStorage = window.localStorage;
const require = chrome.require;
delete chrome.storage; //fake API

if(require == null) {
	alert("Uh-oh, looks like this version of electron isn't rooted yet");
	return;
}

const CspDisarmed = true;

require('https').get("https://github.com/colin969/SimpleDiscordCrypt/raw/master/SimpleDiscordCrypt.user.js", (response) => {
	let data = "";
	response.on('data', (chunk) => data += chunk);
	response.on('end', () => eval(data));
});
