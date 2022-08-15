import os
from cs50 import SQL
from math import floor
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Username John password estrella45%
# Username Bob password -1Estrella3
# Username fatso password samuel56+" "
# wes asd23" "
# lomas qwer123<
# lao xcv23- unused account
# q 1969startreck<
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


# make sure that a secure password is chose
def secure(contra):
    numbers = sum(c.isdigit() for c in contra)
    letters = sum(c.isalpha() for c in contra)
    sola = len(contra) - numbers - letters
    if numbers < 2:
        return 0
    elif letters < 3:
        return 0
    elif sola < 1:
        return 0
    else:
        return 1


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# stock names are not displayed because some names can be way too long
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    # here in post we redirect users to buy or sell more of a owned stock
    if request.method == "POST":

        # checking that either sell or bus is selected
        if not request.form.get("option") or request.form.get("option") == "Action":
            return apology("Choose either buy or sell", 400)
        stock = request.args.get("name")
        act = request.form.get("option").lower()

        # here we display in buy.html some information about the shares when buy is selected
        if act == "buy":
            row = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            deal = lookup(stock)
            if deal != None:
                can_buy = row[0]["cash"]/deal["price"]
                can_buy = floor(can_buy)
                lick = f"With your current money you can buy up to {can_buy} shares of {deal['name']}"
                return render_template(f"{act}.html", inpt=stock, left=lick)
            else:
                return apology("Unexpecteed error", 400)

        # here we display in sell.html some information about the shares when buy is selected
        elif act == "sell":
            row = db.execute("SELECT number_of_shares FROM stocks WHERE user_id = ? and stock_symbol = ?",
                             session["user_id"], stock.upper())
            sl = f"You currently have {row[0]['number_of_shares']} shares of {stock.upper()}"
            return render_template(f"{act}.html", mode=0, select=stock, options="", right=sl)
        else:
            return apology("Unexpecteed error", 400)

    # if method is get here we render the index.html to display the user's stocks
    else:

        # first we update the price of the stocks
        updt = db.execute("SELECT stock_symbol FROM stocks WHERE user_id = ?", session["user_id"])

        # here we see if the user owns any stocks so the table inside index.html can be properly render
        if len(updt) != 0:
            for a in updt:
                pomo = lookup(a["stock_symbol"])
                if pomo != None:
                    rt = db.execute("SELECT number_of_shares FROM stocks WHERE user_id = ? AND stock_symbol = ?",
                                    session["user_id"], a["stock_symbol"])
                    db.execute("UPDATE stocks SET current_price = ?, total = ? WHERE user_id = ? AND stock_symbol = ?",
                               float("{:.2f}".format(pomo["price"])), float(
                                   "{:.2f}".format(rt[0]["number_of_shares"] * pomo["price"])),
                               session["user_id"], a["stock_symbol"])
                else:
                    pass
            rows = db.execute("SELECT * FROM stocks WHERE user_id = ?", session["user_id"])
            sol = db.execute("SELECT SUM(total) FROM stocks WHERE user_id = ?", session["user_id"])
            luna = db.execute("SELECT cash FROM users WHERE id= ?", session["user_id"])
            form = float("{:.2f}".format(sol[0]["SUM(total)"]))
            domo = float("{:.2f}".format(luna[0]["cash"]))
            total = float("{:.2f}".format(form + domo))
            return render_template("index.html", stock=rows, suma=usd(domo), domo=usd(form), total=usd(total), opt=1)
        else:
            luna = db.execute("SELECT cash FROM users WHERE id= ?", session["user_id"])
            domo = float("{:.2f}".format(luna[0]["cash"]))
            return render_template("index.html", stock="", suma=usd(domo), domo=0, total=usd(domo), opt=0)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Ensure stock name was submitted
        if not request.form.get("symbol"):
            return apology("Must provide a stock to buy", 400)

        # Ensure number of shares was submitted
        if not request.form.get("shares"):
            return apology("Must provide a number of shares to buy", 400)
        avalible = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        print(avalible)
        seek = lookup(request.form.get("symbol"))

        # Here we check if the stock submitted exist
        if seek == None:
            return apology("Stock not found", 400)
        socket = request.form.get("shares")

        # here we check that the number of shares is a positive integer number
        try:
            if int(socket) <= 0:
                return apology(f"can't buy a {socket} number of shares", 400)
        except ValueError:
            return apology("Amount of shares to buy must be a integer number", 400)

        # here we check that we have enough money to buy the shares submitted
        money_left = float(avalible[0]["cash"]) - float(seek["price"])*int(socket)
        if money_left < 0:
            return apology("not enough money to buy that many shares", 400)

        # here we update the cash after the buy
        db.execute("UPDATE users SET cash = ? WHERE id = ?", float("{:.2f}".format(money_left)), session["user_id"])
        rows = db.execute("SELECT * FROM stocks WHERE user_id = ? AND stock_symbol = ?", session["user_id"],
                          request.form.get("symbol").upper())

        # here if the stock bought was previously registered we update the shares, price and total (stock*shares)
        # in the stock database that keep record of what stocks the user owns, if the stock was not registered
        # we insert a new row in the stock database with the proper information
        if len(rows) == 1:
            new_shares = rows[0]["number_of_shares"] + int(socket)
            total_value = float(seek["price"])*new_shares
            db.execute("UPDATE stocks SET number_of_shares = ?, current_price = ?, total = ?  WHERE user_id = ? AND stock_symbol = ?",
                       new_shares, float("{:.2f}".format(seek["price"])), float("{:.2f}".format(total_value)), session["user_id"], request.form.get("symbol").upper())
        else:
            total_value = float(seek["price"])*int(socket)
            db.execute("INSERT INTO stocks (user_id, stock_symbol, number_of_shares, current_price, total) VALUES(?, ?, ?, ?, ?)",
                       session["user_id"], request.form.get("symbol").upper(), int(socket), float("{:.2f}".format(seek["price"])),
                       float("{:.2f}".format(total_value)))

        # here in the transactions database we keep track of every buy operation made by the user
        db.execute("INSERT INTO transactions (session_id, symbol, operation, shares, price) VALUES(?, ?, ?, ?, ?)",
                   session["user_id"], request.form.get("symbol").upper(), "buy", int(socket), float("{:.2f}".format(seek["price"])))

        flash("stock bought successfully")
        return redirect("/", 302)

    # if method is get we render the buy page with some information about the user cash
    else:
        dash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        return render_template("buy.html", left=f"Current cash {usd(dash[0]['cash'])}")


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Show history of transactions"""

    # here we render the transaction history of the user with the transactions database
    # if there is or not any information in the database the page is render in different ways
    if request.method == "GET":
        loma = db.execute("SELECT * FROM transactions WHERE session_id = ?", session["user_id"])
        if len(loma) != 0:
            return render_template("history.html", table=loma, ruta=1)
        else:
            return render_template("history.html", table="", ruta=0)

    # for any reason if a post method is pass we raise an error
    else:
        return apology("Unexpected error", 400)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/", 302)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/", 302)


@app.route("/quote", methods=["POST", "GET"])
@login_required
def quote():

    # here the user can get information about a stock current price
    if request.method == "POST":

        # first we check that a stock name is submitted
        if not request.form.get("symbol"):
            return apology("Must provide stock name", 400)
        place = lookup(request.form.get("symbol"))

        # then we check if we can find any information about the stock
        # if we can we reload the page with the information found
        if place == None:
            return apology("Stock not found", 400)
        phrase = "A share of {space} ({expand}) is currently value at {flavour}".format(space=place["name"],
                                                                                        expand=place["symbol"], flavour=usd(place["price"]))
        return render_template("quote.html", info=phrase)

    # here we render the quote page when a get method is pass
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure username was selected
        if not request.form.get("username"):
            return apology("Must provide username", 400)

        # Ensure password was selected
        elif not request.form.get("password"):
            return apology("Must provide password", 400)

        # Ensure password confirmation
        elif not request.form.get("confirmation"):
            return apology("Must confirm password", 400)

        # if username already exits return apology
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) == 1:
            invalid = rows[0]["username"]
            return apology(f"The username {invalid} is not avalible", 400)

        # check that confirmation is equal to password
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password confirmation does not match password", 400)

        # check that the password has at least 6 characters
        if len(request.form.get("password")) < 6:
            return apology("Password must contain at least 6 chararcters", 400)

        # checking that the passwors has at least 3 letters, 2 numbers and one symbol
        if secure(request.form.get("password")) == 0:
            return apology("Password must contain at least 2 numbers, 1 symbol and 3 letters", 400)

        # here we save in the users database the information of the new user
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))
        valid = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Remember that new user has logged in
        session["user_id"] = valid[0]["id"]

        # Redirect user to home page
        flash("acount created successfully")
        return redirect("/", 302)

    # here we render the register page when a get method is pass
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        # first we check that the user has selected any valid stock
        # if he didnt an error is raise with 2 different messages
        # one if the user does not has any stock to sell and other
        # if the user has any stock to sell
        if not request.form.get("symbol") or request.form.get("symbol") == "Stocks":
            upt = db.execute("SELECT stock_symbol FROM stocks WHERE user_id = ?", session["user_id"])
            if len(upt) != 0:
                return apology("Select a stock", 400)
            else:
                return apology("You need to buy a stock first before being able to sell", 400)

        # here we check that a number of shares was submitted
        if not request.form.get("shares"):
            return apology("Must provide a number of shares to sell", 400)

        # here we check that the shares submitted are a positive integer number
        zapallo = request.form.get("shares")
        try:
            if int(zapallo) <= 0:
                return apology(f"can't buy a {zapallo} number of shares", 400)
        except ValueError:
            return apology("Amount of shares to sell must be a integer number", 400)

        # here we see if the price of the stock selected can be found
        wow = lookup(request.form.get("symbol").upper())
        if wow == None:
            return apology("Unexpecteed error", 400)
        raw = db.execute("SELECT * FROM stocks WHERE user_id = ? AND stock_symbol = ?",
                         session["user_id"], request.form.get("symbol").upper())

        # here we check that we have any shares of the stock we want to sell
        if len(raw) != 1:
            return apology(f"You dont have any shares of {request.form.get('symbol').upper()}", 400)

        # here we check that the amount of shares to sell is less than the shares we own
        if int(zapallo) > raw[0]["number_of_shares"]:
            return apology("You don't have that many shares of that stock to sell ", 400)
        chs = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        new_cash = float("{:.2f}".format(chs[0]["cash"] + int(zapallo) * wow["price"]))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])

        # here we save the information about the sell transaction in the transactions database of the user
        db.execute("INSERT INTO transactions (session_id, symbol, operation, shares, price) VALUES(?, ?, ?, ?, ?)",
                   session["user_id"], request.form.get("symbol").upper(), "sell", int(zapallo), float("{:.2f}".format(wow["price"])))
        new_shares = raw[0]["number_of_shares"] - int(zapallo)

        # if after the sell we have 0 shares of the stock the information
        # about that share is deleted from the stock database of the user
        # if we still have shares after the sell we update the number of shares,
        # price and total (shares*price) of the stock sold by the user
        if new_shares == 0:
            db.execute("DELETE FROM stocks WHERE user_id = ? AND stock_symbol = ?",
                       session["user_id"], request.form.get("symbol").upper())
        else:
            new_total = wow["price"]*new_shares
            db.execute("UPDATE stocks SET number_of_shares = ?, current_price = ?, total = ? WHERE user_id = ? AND stock_symbol = ?",
                       new_shares, float("{:.2f}".format(wow["price"])), float("{:.2f}".format(new_total)), session["user_id"], request.form.get("symbol").upper())

        flash("Stock sold successfully")
        return redirect("/", 302)

    # here we render the sell page when a get method is pass
    # when rendering we pass the current stock owned by the user
    # to determinate how the page is going to be display
    else:
        upt = db.execute("SELECT stock_symbol FROM stocks WHERE user_id = ?", session["user_id"])
        fluttershy = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        if len(upt) != 0:
            return render_template("sell.html", options=upt, mode=1, right=f"Current cash {usd(fluttershy[0]['cash'])}")
        else:
            return render_template("sell.html", options="", mode=0, right=f"Current cash {usd(fluttershy[0]['cash'])}")


# a route to handling an async js function
# if status code is 203 information about
# the amount of shares the user can buy of
# a stock is returned to the buy.html page
@app.route("/requestb", methods=["GET", "POST"])
@login_required
def how_much():
    if request.method == "GET":
        sal = request.args.get("buy")
        desk = lookup(sal)
        if desk != None:
            row = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            can_buy = row[0]["cash"]/desk["price"]
            print(desk["price"])
            can_buy = floor(can_buy)
            flick = f"With your current money you can buy up to {can_buy} shares of {desk['name']}"
            return flick, 203
        else:
            return "", 400
    else:
        pepper = request.args.get("buy")
        dot = pepper.split("_")
        doll = lookup(dot[0])
        if doll != None:
            try:
                if int(dot[1]) <= 0:
                    return "", 400
                else:
                    red = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
                    hop = float(red[0]["cash"] - int(dot[1])*doll["price"])
                    if hop < 0:
                        msg = f"You don't have the money to buy {int(dot[1])} shares of {dot[0].upper()}"
                        return msg, 203
                    else:
                        msg = f"The buy of {int(dot[1])} shares would let you with {usd(hop)} in cash"
                        return msg, 203
            except ValueError:
                return "", 400
        else:
            return "", 400


# a route to handling an async js function
# if status code is 200 the display of the
# configuration.html page is changed when
# any of the 2 options of the page is selected
@app.route("/settings", methods=["POST"])
@login_required
def changes():
    if request.method == "POST":
        if request.args.get("cash") == "cash":
            return render_template("recharge.html"), 200
        if request.args.get("cash") == "pass":
            return render_template("change.html"), 200
        return "", 400
    return "", 400


@app.route("/configuration", methods=["GET"])
@login_required
def settings():

    # here we render the configuration page when a get method is pass
    return render_template("configuration.html")


# here we hand the change of password
# when that options is submitted
# from the configuration page
# here we check that the same
# conditions for the password when
# a user is registering are met
@app.route("/passw", methods=["POST"])
@login_required
def passw():
    if request.method == "POST":
        if not request.form.get("newpassword"):
            return apology("Must provide password", 400)
        if not request.form.get("confirmation"):
            return apology("Must confirm password", 400)
        if request.form.get("newpassword") != request.form.get("confirmation"):
            return apology("Password confirmation does not match password", 400)
        if len(request.form.get("newpassword")) < 6:
            return apology("Password must contain at least 6 characters")
        if secure(request.form.get("newpassword")) == 0:
            return apology("A new password must contain at least 3 letters, 1 symbol and 2 numbers", 400)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(
            request.form.get("newpassword")), session["user_id"])
        flash("Password changed successfully")
        return render_template("configuration.html")
    else:
        return "", 400


# here we hand the adding of cash
# when that options is submitted
# from the configuration page
# here we check that something
# that is a positive integer number
# whose value is not more than
# 15000 is submitted
@app.route("/cashe", methods=["POST"])
@login_required
def cashh():
    if request.method == "POST":
        if not request.form.get("amount"):
            return apology("Must provide a cash amount", 400)
        some = request.form.get("amount")
        try:
            if int(some) <= 0:
                return apology("Cash amount cant be a negative number", 400)
        except ValueError:
            return apology("Cash amount has to be a integer number", 400)
        if float(some) > 15000:
            return apology("Max ammount of money that can be added is 15000 usd", 400)
        cahs = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        new = float("{:.2f}".format(float(some) + cahs[0]["cash"]))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new, session["user_id"])
        flash(f"{usd(int(some))} USD where added to your cash")
        return render_template("configuration.html")
    else:
        return "", 400


# a route to handling an async js function
# if status code is 203 information about
# the amount of cash a user have or about
# how much cash a user can get when selling
# a number of shares from a stock is
# returned to the sell.html page
@app.route("/gains", methods=["POST", "GET"])
@login_required
def gain():
    if request.method == "POST":
        pepper = request.args.get("sell")
        dot = pepper.split("_")
        doll = lookup(dot[0])
        if doll != None:
            try:
                if int(dot[1]) > 0:
                    money = float("{:.2f}".format(int(dot[1]) * doll["price"]))
                    sos = db.execute("SELECT number_of_shares FROM stocks WHERE user_id = ? and stock_symbol = ?",
                                     session["user_id"], dot[0].upper())
                    if int(dot[1]) <= sos[0]["number_of_shares"]:
                        msg = f"Selling {dot[1]} stocks of {dot[0]} would give you {usd(money)}"
                        return msg, 203
                    else:
                        msg = f"You don't have that many shares of {dot[0].upper()} to sell"
                        return msg, 203
                else:
                    return "", 400
            except ValueError:
                return "", 400
        else:
            return "", 400
    else:
        if not request.args.get("precio"):
            return "", 400
        lamento = request.args.get("precio")
        sos = db.execute("SELECT number_of_shares FROM stocks WHERE user_id = ? and stock_symbol = ?",
                         session["user_id"], lamento.upper())
        if len(sos) != 0:
            ggf = f"You currently have {sos[0]['number_of_shares']} shares of {lamento.upper()}"
            return ggf, 203
        else:
            return "", 400

