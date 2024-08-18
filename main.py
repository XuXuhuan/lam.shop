from flask import Flask, render_template, redirect, url_for, session, request
import math
import os
import bcrypt
import sqlite3

multipliers = [10, 8, 6, 3.5, 2, 1.2, 1, 0.7, 0.5]

app = Flask(__name__)
app.secret_key = os.urandom(20).hex()

@app.route('/', methods=["GET", "POST"])
def index():
    conn = sqlite3.connect("lamshop.db")
    cursor = conn.cursor()
    if "username" not in session:
        return redirect(url_for("login"))
    elif request.method == "POST":
        item_name = request.form.get("item")
        item = cursor.execute("""
            SELECT *
            FROM items
            WHERE name = ?;
        """, (item_name,)).fetchone()
        item_id = item[0]
        user = cursor.execute("""
            SELECT *
            FROM users
            WHERE username = ?;
        """, (session["username"],)).fetchone()
        check_already_bought = cursor.execute("""
            SELECT *
            FROM users
            LEFT JOIN buy_history
            ON buy_history.user_id = users.id
            WHERE users.username = ?
            AND buy_history.item_id = ?;
        """, (session["username"], item_id)).fetchone()
        if item is not None and check_already_bought is None:
            if user[3] >= item[2]:
                new_lamcoin = math.floor((user[3] - item[2]) * 100) / 100
                cursor.execute("""
                    UPDATE users
                    SET lamcoin = ?
                    WHERE username = ?;
                """, (new_lamcoin, session["username"]))
                cursor.execute("""
                    INSERT INTO buy_history (user_id, item_id)
                    VALUES (?, ?);
                """, (user[0], item[0]))
                conn.commit()
    items = cursor.execute("""
        SELECT name, price, imgfilename
        FROM items;
    """).fetchall()
    bought_items = cursor.execute("""
        SELECT items.name, items.price, items.imgfilename
        FROM users
        LEFT JOIN buy_history
        ON buy_history.user_id = users.id
        LEFT JOIN items
        ON buy_history.item_id = items.id
        WHERE users.username = ?;
    """, (session["username"],)).fetchall()
    user_details = cursor.execute("""
    SELECT users.lamcoin, items.name, items.price, items.imgfilename
    FROM users
    LEFT JOIN items
    ON users.equipped_item = items.id
    WHERE username = ?;""", (session["username"],)).fetchone()
    conn.close()
    lamcoin = int(user_details[0]) if user_details[0] % 1 == 0 else user_details[0]
    equipped_item = {
        user_details[1] : {
            "price": user_details[2],
            "imgfilename": user_details[3]
        }
    }
    owned_items = {x[0] : {"price": int(x[1]) if x[1] % 1 == 0 else x[1], "imgfilename": x[2]} for x in bought_items} if bought_items[0][0] is not None else {}
    unowned_items = {}
    for x in items:
        if x[0] not in owned_items.keys():
            price = int(x[1]) if x[1] % 1 == 0 else x[1]
            unowned_items[x[0]] = {"price": price, "imgfilename": x[2]}
    return render_template("index.html", lamcoin=lamcoin, owned_items=owned_items, unowned_items=unowned_items, equipped_item=equipped_item)

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "username" in session:
            return redirect(url_for("index"))
        else:
            return render_template("login.html")
    else:
        conn = sqlite3.connect("lamshop.db")
        cursor = conn.cursor()
        input_user = request.form.get("username")
        input_password = request.form.get("password").encode("utf-8")
        queried_password = cursor.execute("""
            SELECT password
            FROM users
            WHERE username = ?;
        """, (input_user,)).fetchone()
        conn.close()
        if queried_password is not None:
            if bcrypt.checkpw(input_password, queried_password[0].encode("utf-8")):
                session["username"] = input_user
                session.permanent = True
                return redirect(url_for("index"))
            else:
                return render_template("login.html", message="Incorrect password or username.")
        else:
            return render_template("login.html", message="Incorrect password or username.")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        conn = sqlite3.connect("lamshop.db")
        cursor = conn.cursor()
        username = request.form.get("username")
        password = request.form.get("password")
        trimmed_password = "".join(password.split())
        confirm_password = request.form.get("confirmPassword")
        if password != confirm_password:
            return render_template("signup.html", message="Passwords do not match.")
        elif not username.isalnum():
            return render_template("signup.html", message="Username may only contain alphanumerical characters.")
        elif len(username) < 5 or len(username) > 20:
            return render_template("signup.html", message="Please enter a valid username of 5-20 characters.")
        elif len(trimmed_password) < 8:
            return render_template("signup.html", message="Please enter a password of at least 8 characters.")
        else:
            check_exists = cursor.execute("""
                SELECT username
                FROM users
                WHERE username = ?;
            """, (username,)).fetchone()
            if check_exists is not None:
                return render_template("signup.html", message="User already exists.")
            else:
                salt = bcrypt.gensalt()
                password_bytes = password.encode("utf-8")
                hashed_pw = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
                cursor.execute("""
                    INSERT INTO users (username, password, lamcoin)
                    VALUES (?, ?, ?)
                """, (username, hashed_pw, 100))
                conn.commit()
                conn.close()
                return redirect(url_for("login"))

@app.route('/logout', methods=["POST"])
def logout():
    if "username" in session:
        session.clear()
    return redirect(url_for("login"))

@app.route('/equip', methods=["POST"])
def equip():
    if "username" not in session:
        return redirect(url_for("login"))
    else:
        conn = sqlite3.connect("lamshop.db")
        cursor = conn.cursor()
        user_details = cursor.execute("""
            SELECT users.lamcoin, items.name
            FROM users
            LEFT JOIN items
            ON users.equipped_item = items.id
            WHERE username = ?;""", (session["username"],)).fetchone()
        if request.form.get("item") == user_details[1]:
            cursor.execute("""
                            UPDATE users
                            SET equipped_item = NULL
                            WHERE username = ?;""", (session["username"],))
            conn.commit()
        else:
            bought_items = cursor.execute("""
                SELECT items.id, items.name, items.price, items.imgfilename
                FROM users
                LEFT JOIN buy_history
                ON buy_history.user_id = users.id
                LEFT JOIN items
                ON buy_history.item_id = items.id
                WHERE users.username = ?;""", (session["username"],)).fetchall()
            found = False
            item_id = None
            for row in bought_items:
                if row[1] == request.form.get("item"):
                    item_id = row[0]
                    found = True
            if found:
                cursor.execute("""
                UPDATE users
                SET equipped_item = ?
                WHERE username = ?""", (item_id, session["username"]))
                conn.commit()
        conn.close()
    return redirect(url_for("index"))

@app.route('/gamble', methods=["GET", "POST"])
def gamble():
    if "username" not in session:
        return redirect(url_for("login"))
    elif request.method == "GET":
        conn = sqlite3.connect("lamshop.db")
        cursor = conn.cursor()
        ballskinurl = ""
        equipped_item = cursor.execute("""
            SELECT users.lamcoin, items.name, items.imgfilename
            FROM users
            LEFT JOIN items
            ON users.equipped_item = items.id
            WHERE username = ?;""", (session["username"],)).fetchone()
        conn.close()
        if equipped_item[1] is not None:
            ballskinurl = url_for('static', filename='assets/' + equipped_item[2])
        return render_template("gamble.html", lamcoin=int(equipped_item[0]) if equipped_item[0] % 1 == 0 else equipped_item[0], ballskinurl=ballskinurl)

@app.route('/drop_ball', methods=["POST"])
def drop_ball():
    if "username" not in session:
        return "error"
    else:
        ball_value = None
        try:
            ball_value = float(request.form.get("ballvalue"))
        except ValueError:
            return "error"
        
        if ball_value > 0 and ball_value * 100 % 1 == 0:
            conn = sqlite3.connect("lamshop.db")
            cursor = conn.cursor()
            lamcoin = cursor.execute("""
                                     SELECT lamcoin
                                     FROM users
                                     WHERE username = ?""", (session["username"],)).fetchone()[0]
            if ball_value <= lamcoin:
                new_lamcoin = math.floor((lamcoin - ball_value) * 100) / 100
                cursor.execute("""
                                UPDATE users
                                SET lamcoin = ?
                                WHERE username = ?""", (new_lamcoin, session["username"]))
                conn.commit()
                conn.close()
                return str(new_lamcoin)
            else:
                return "insufficient funds"
        else:
            return "error"

@app.route('/receive_ball', methods=["POST"])
def receive_ball():
    if "username" not in session:
        return "error"
    else:
        ball_value = None
        multiplier = None
        try:
            ball_value = float(request.form.get("ballvalue"))
            multiplier = float(request.form.get("multiplier"))
        except ValueError:
            return "error"

        if ball_value > 0 and ball_value * 100 % 1 == 0 and multiplier in multipliers:
            conn = sqlite3.connect("lamshop.db")
            cursor = conn.cursor()
            lamcoin = cursor.execute("""
                                     SELECT lamcoin
                                     FROM users
                                     WHERE username = ?""", (session["username"],)).fetchone()[0]
            new_lamcoin = math.floor((lamcoin + ball_value * multiplier) * 100) / 100
            cursor.execute("""
                            UPDATE users
                            SET lamcoin = ?
                            WHERE username = ?""", (new_lamcoin, session["username"]))
            conn.commit()
            conn.close()
            return str(new_lamcoin)
        else:
            return "error"


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)