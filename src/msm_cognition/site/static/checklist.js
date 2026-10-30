// Send checklist clicks to the local server, then reload to show the
// regenerated page. On a generated island page each item also gets minus and
// plus buttons for counts above one; its checkbox only moves between 0 and 1.

const ISLAND_PAGE = /^inventory\/islands\/[^/]+\.md$/;

function showStatus(text, isError) {
	const box = document.getElementById("status");
	box.textContent = text;
	box.className = isError ? "error" : "";
	box.hidden = false;
}

async function send(input, action) {
	document.querySelectorAll("input[data-line], .count button").forEach((el) => { el.disabled = true; });
	try {
		const response = await fetch("/__edit/checklist", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				path: input.dataset.path,
				line: Number(input.dataset.line),
				text: input.dataset.text,
				action: action,
			}),
		});
		const result = await response.json();
		if (!response.ok) {
			throw new Error(result.error || response.statusText);
		}
		try {
			sessionStorage.setItem("msm-status", result.message + ". " + result.status);
			sessionStorage.setItem("msm-scroll", String(window.scrollY));
		} catch (e) {
			// Storage can be unavailable; the reload still shows the change.
		}
		location.reload();
	} catch (error) {
		showStatus(error.message, true);
		setTimeout(() => location.reload(), 2500);
	}
}

function countOf(input) {
	const match = input.dataset.text.match(/ x(\d+)(?: \([^)]*\))?$/);
	if (match) {
		return Number(match[1]);
	}
	return input.checked ? 1 : 0;
}

function addCountButtons(input) {
	const count = countOf(input);
	const group = document.createElement("span");
	group.className = "count";
	for (const [label, action, title] of [["-", "decrement", "One fewer"], ["+", "increment", "One more"]]) {
		const button = document.createElement("button");
		button.type = "button";
		button.textContent = label;
		button.title = title;
		button.disabled = action === "decrement" && count === 0;
		button.addEventListener("click", () => send(input, action));
		group.append(button);
	}
	input.closest("label").after(group);
	if (count > 1) {
		input.disabled = true;
		input.title = "Use the minus button to lower a count above one.";
	}
}

document.addEventListener("DOMContentLoaded", () => {
	try {
		const message = sessionStorage.getItem("msm-status");
		const scroll = sessionStorage.getItem("msm-scroll");
		sessionStorage.removeItem("msm-status");
		sessionStorage.removeItem("msm-scroll");
		if (scroll) {
			window.scrollTo(0, Number(scroll));
		}
		if (message) {
			showStatus(message, false);
			setTimeout(() => { document.getElementById("status").hidden = true; }, 5000);
		}
	} catch (e) {
		// Storage can be unavailable; nothing to restore.
	}
	for (const input of document.querySelectorAll("input[data-line]")) {
		input.addEventListener("change", () => send(input, input.checked ? "check" : "uncheck"));
		if (ISLAND_PAGE.test(input.dataset.path)) {
			addCountButtons(input);
		}
	}
});
