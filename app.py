from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, flash, g
import psycopg2
from passlib.handlers.sha2_crypt import sha512_crypt
import os
from flask.helpers import send_file
from io import BytesIO
import datetime

app = Flask(__name__)
app.secret_key = ''
database = ''

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user', None)

        email = request.form['email']
        password = request.form['password']

        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = '" +
                  email+"' AND password = '"+password+"'")
        r = c.fetchall()

        for i in r:
            if (email == i[3] and password == i[4]):
                session['user'] = i[0]
                return redirect(url_for('home'))
        else:
            flash("Invalid Email or Password", 'invalid')

        conn.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first = request.form['first_name']
        last = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        profile = request.files['profile']

        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT email FROM users")
        rs = c.fetchall()
        for rs in rs:
            if email in rs:
                flash("Email already associated with an account", 'validemail')
                break
        else:
            c.execute("""
            INSERT INTO users (firstname, lastname, email, password, profilepic) VALUES (%s, %s, %s, %s, %s)""", (first, last, email, password, profile.read()))
            conn.commit()
            flash(
                "Registration successfull ! You can now log in to your account ", 'register')
        conn.close

        return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchall()

        c.execute("SELECT SUM(income) FROM income WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalincome = c.fetchall()

        c.execute("SELECT SUM(amount) FROM expense WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalexpense = c.fetchall()

        context = {
            'user': session['user'],
            'rs': rs,
            'totalincome': totalincome,
            'totalexpense': totalexpense
        }

        if request.method == 'POST':
            phone = request.form['phone']
            password = request.form['password']
            pic = request.files['pic']

            if phone != '':
                c.execute("UPDATE users SET phone = '"+phone +
                          "' WHERE id = '"+str(session['user'])+"'")
                conn.commit()

            if password != '':
                c.execute("UPDATE users SET password = '"+password +
                          "' WHERE id = '"+str(session['user'])+"'")
                conn.commit()

            if pic != '':
                c.execute("""
                UPDATE users SET profilepic = %s WHERE id = %s""", (pic.read(), session['user']))
                conn.commit()

            flash("Data Updated", 'profile')

        conn.close()
        return render_template('home.html', **context)

    return redirect(url_for('login'))


@app.route('/profile<int:id>')
def profile(id):
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = '"+str(id)+"'")
        rs = c.fetchone()
        certificate = rs[5]

        return send_file(BytesIO(certificate), attachment_filename='flask.png', as_attachment=False)

        return redirect(url_for('home'))
        conn.close()


@app.route('/income', methods=['GET', 'POST'])
def income():
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchall()

        c.execute("SELECT SUM(income) FROM income WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalincome = c.fetchall()

        c.execute("SELECT SUM(amount) FROM expense WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalexpense = c.fetchall()

        if request.method == 'POST':
            uid = session['user']
            source = request.form['source']
            income = request.form['money']
            date = request.form['date']

            yyyy, mm, dd = map(int, date.split('-'))
            fdate = str(dd)+"-"+str(mm)+"-"+str(yyyy)
            day = datetime.date(yyyy, mm, dd).strftime('%A')

            c.execute("""
            INSERT INTO income (uid, source, income, date, day, ogdate) VALUES (%s, %s, %s, %s, %s, %s)""", (uid, source, income, fdate, day, date))
            conn.commit()

            flash("New Income added successfully !", 'income')

            return redirect(url_for('income'))

        c.execute("SELECT * FROM income WHERE uid = '" +
                  str(session['user'])+"' ORDER BY id DESC LIMIT 5")
        income = c.fetchall()

        context = {
            'user': session['user'],
            'rs': rs,
            'income': income,
            'totalincome': totalincome,
            'totalexpense': totalexpense,
        }
        conn.close()
        return render_template('income.html', **context)

    return redirect(url_for('login'))


@app.route('/deleteincome<int:id>')
def deleteincome(id):
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("DELETE FROM income WHERE id = '"+str(id)+"'")
        conn.commit()
        conn.close()

        flash('Income deleted !', 'deleteincome')

        return redirect(url_for('income'))

    return redirect(url_for('login'))


@app.route('/updateincome<int:id>', methods=['GET', 'POST'])
def updateincome(id):
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchall()

        c.execute("SELECT * FROM income WHERE id = '"+str(id)+"'")
        r = c.fetchone()

        c.execute("SELECT * FROM income WHERE uid = '" +
                  str(session['user'])+"' ORDER BY id DESC LIMIT 5")
        income = c.fetchall()

        c.execute("SELECT SUM(income) FROM income WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalincome = c.fetchall()

        c.execute("SELECT SUM(amount) FROM expense WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalexpense = c.fetchall()

        if request.method == 'POST':
            source = request.form['source']
            income = request.form['money']
            date = request.form['date']

            yyyy, mm, dd = map(int, date.split('-'))
            fdate = str(dd)+"-"+str(mm)+"-"+str(yyyy)
            day = datetime.date(yyyy, mm, dd).strftime('%A')

            c.execute("""
            UPDATE income SET (source, income, date, day, ogdate) = (%s, %s, %s, %s, %s) WHERE id = %s""", (source, income, fdate, day, date, id))
            conn.commit()

            flash("Income updated successfully !", 'updateincome')

            conn.close()

            return redirect(url_for('income'))

        context = {
            'rs': rs,
            'r': r,
            'income': income,
            'totalincome': totalincome,
            'totalexpense': totalexpense,
        }
        conn.close()
        return render_template('updateincome.html', **context)
    return redirect(url_for('login'))


@app.route('/expense', methods=['GET', 'POST'])
def expense():
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchall()

        c.execute("SELECT SUM(income) FROM income WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalincome = c.fetchall()

        c.execute("SELECT SUM(amount) FROM expense WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalexpense = c.fetchall()

        if request.method == 'POST':
            uid = session['user']
            source = request.form['source']
            expense = request.form['money']
            date = request.form['date']

            yyyy, mm, dd = map(int, date.split('-'))
            fdate = str(dd)+"-"+str(mm)+"-"+str(yyyy)
            day = datetime.date(yyyy, mm, dd).strftime('%A')

            c.execute("""
            INSERT INTO expense (uid, source, amount, date, day, ogdate) VALUES (%s, %s, %s, %s, %s, %s)""", (uid, source, expense, fdate, day, date))
            conn.commit()

            flash("New Expense added successfully !", 'expense')

            return redirect(url_for('expense'))

        c.execute("SELECT * FROM expense WHERE uid = '" +
                  str(session['user'])+"' ORDER BY id DESC LIMIT 5")
        expense = c.fetchall()

        context = {
            'user': session['user'],
            'rs': rs,
            'expense': expense,
            'totalincome': totalincome,
            'totalexpense': totalexpense,
        }
        conn.close()
        return render_template('expense.html', **context)

    return redirect(url_for('login'))


@app.route('/deleteexpense<int:id>')
def deleteexpense(id):
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("DELETE FROM expense WHERE id = '"+str(id)+"'")
        conn.commit()
        conn.close()

        flash('Expense deleted !', 'deleteexpense')

        return redirect(url_for('expense'))

    return redirect(url_for('login'))


@app.route('/updateexpense<int:id>', methods=['GET', 'POST'])
def updateexpense(id):
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchall()

        c.execute("SELECT * FROM expense WHERE id = '"+str(id)+"'")
        r = c.fetchone()

        c.execute("SELECT * FROM expense WHERE uid = '" +
                  str(session['user'])+"' ORDER BY id DESC LIMIT 5")
        expense = c.fetchall()

        c.execute("SELECT SUM(income) FROM income WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalincome = c.fetchall()

        c.execute("SELECT SUM(amount) FROM expense WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalexpense = c.fetchall()

        if request.method == 'POST':
            source = request.form['source']
            expense = request.form['money']
            date = request.form['date']

            yyyy, mm, dd = map(int, date.split('-'))
            fdate = str(dd)+"-"+str(mm)+"-"+str(yyyy)
            day = datetime.date(yyyy, mm, dd).strftime('%A')

            c.execute("""
            UPDATE expense SET (source, amount, date, day, ogdate) = (%s, %s, %s, %s, %s) WHERE id = %s""", (source, expense, fdate, day, date, id))
            conn.commit()

            flash("Expense updated successfully !", 'updateexpense')

            conn.close()

            return redirect(url_for('expense'))

        context = {
            'rs': rs,
            'r': r,
            'expense': expense,
            'totalincome': totalincome,
            'totalexpense': totalexpense,
        }
        conn.close()
        return render_template('updateexpense.html', **context)
    return redirect(url_for('login'))


@app.route('/stats')
def stats():
    if g.user:
        conn = psycopg2.connect(database)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE id = '"+str(session['user'])+"'")
        rs = c.fetchall()

        c.execute("SELECT SUM(income) FROM income WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalincome = c.fetchall()

        c.execute("SELECT SUM(amount) FROM expense WHERE uid = '" +
                  str(session['user'])+"' GROUP BY user")
        totalexpense = c.fetchall()

        c.execute("SELECT ROUND(SUM(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"'")
        income = c.fetchone()

        c.execute("SELECT ROUND(SUM(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"'")
        expense = c.fetchone()

        if income[0] > expense[0]:
            flash((income[0]-expense[0])/7, 'profit')
        elif income[0] < expense[0]:
            flash((expense[0]-income[0])/7, 'loss')
        else:
            flash("0", 'neutral')

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Sunday'")
        sunday_income = c.fetchone()

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Monday'")
        monday_income = c.fetchone()

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Tuesday'")
        tuesday_income = c.fetchone()

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Wednesday'")
        wednesday_income = c.fetchone()

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Thursday'")
        thursday_income = c.fetchone()

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Friday'")
        friday_income = c.fetchone()

        c.execute("SELECT ROUND(AVG(income), 2) FROM income WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Saturday'")
        saturday_income = c.fetchone()

        data = [
            ("Sunday", sunday_income[0]),
            ("Monday", monday_income[0]),
            ("Tuesday", tuesday_income[0]),
            ("Wednesday", wednesday_income[0]),
            ("Thursday", thursday_income[0]),
            ("Friday", friday_income[0]),
            ("Saturday", saturday_income[0]),
        ]

        labels = [row[0] for row in data]
        values = [row[1] for row in data]
        values = [int(i or 0) for i in values]

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Sunday'")
        sunday_expense = c.fetchone()

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Monday'")
        monday_expense = c.fetchone()

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Tuesday'")
        tuesday_expense = c.fetchone()

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Wednesday'")
        wednesday_expense = c.fetchone()

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Thursday'")
        thursday_expense = c.fetchone()

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Friday'")
        friday_expense = c.fetchone()

        c.execute("SELECT ROUND(AVG(amount), 2) FROM expense WHERE uid = '" +
                  str(session['user'])+"' AND day = 'Saturday'")
        saturday_expense = c.fetchone()

        data = [
            ("Sunday", sunday_expense[0]),
            ("Monday", monday_expense[0]),
            ("Tuesday", tuesday_expense[0]),
            ("Wednesday", wednesday_expense[0]),
            ("Thursday", thursday_expense[0]),
            ("Friday", friday_expense[0]),
            ("Saturday", saturday_expense[0]),
        ]

        expensevalues = [row[1] for row in data]
        expensevalues = [int(i or 0) for i in expensevalues]

        context = {
            'user': session['user'],
            'rs': rs,
            'labels': labels,
            'values': values,
            'expensevalues': expensevalues,
            'totalincome': totalincome,
            'totalexpense': totalexpense,
        }

        conn.close()
        return render_template('stats.html', **context)
    return redirect(url_for('login'))


@ app.before_request
def before_request():
    g.user = None

    if 'user' in session:
        g.user = session['user']


if __name__ == '__main__':
    app.run(debug=True)
