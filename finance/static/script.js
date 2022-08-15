// this function makes an asynchronous request
// to app.py to change the contents of buy.html
// to show if app.py returns 203 how many shares
// the user can buy of a stock
async function consult() {
    var input = document.getElementById("symbol").value;
    if (!input) {
        return;
    }
    let x = await fetch("/requestb?buy=" + input);
    if (x.ok) {
        let y = await x.text();
        document.getElementById("placeholder").innerHTML = y;
    } else {
        return;
    }
}

// this function makes an asynchronous request
// to app.py to change the contents of buy.html
// to show if app.py returns 203 if the user has
// the money to buy the inputted shares or how
// much cash the user would have left after
// buying the shares
async function info() {
    var input = document.getElementById("symbol").value;
    var share = document.getElementById("numbershare").value;
    if (!input) {
        return;
    }
    if (!share) {
        return;
    }
    let sup = input.concat("_", share);
    let x = await fetch("/requestb?buy=" + sup, { method: "POST" });
    if (x.ok) {
        let y = await x.text();
        document.getElementById("placeholder").innerHTML = y;
    } else {
        return;
    }
}

// this function makes an asynchronous request
// to app.py to change the contents of configuration.html
// to show if app.py returns 203 the change password menu
// if the user wants to change its password or the
// add cash menu if the user want to add cash to its account
async function seek(word) {
    let x = await fetch("/settings?cash=" + word, { method: "POST" });
    let y = await x.text();
    if (x.ok) {
        document.getElementById("ocultop").innerHTML = y;
    } else {
        return;
    }
}

// this function makes an asynchronous request
// to app.py to change the contents of sell.html
// to show if app.py returns 203 if the user has
// the amount of shares inputted to sell or how
// much money the user would receive if he sell its shares
async function gain() {
    var input = document.getElementById("only").value;
    var num = document.getElementById("num").value;
    if (!input) {
        return;
    }
    if (!num) {
        return;
    }
    let jn = input.concat("_", num);
    let x = await fetch("/gains?sell=" + jn, { method: "POST" });
    if (x.ok) {
        let y = await x.text();
        document.getElementById("placeholder").innerHTML = y;
    } else {
        return;
    }
}

// this function makes an asynchronous request
// to app.py to change the contents of sell.html
// to show if app.py returns 203 how many shares
// the user can sell of a stock
async function consulta() {
    var input = document.getElementById("only").value;
    if (!input) {
        return;
    }
    let x = await fetch("/gains?precio=" + input);
    let y = await x.text();
    if (x.ok) {
        document.getElementById("placeholder").innerHTML = y;
    } else {
        return;
    }
}