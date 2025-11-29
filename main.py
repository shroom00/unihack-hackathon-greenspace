from flask import Flask, url_for, render_template


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contact.html")
def contact():
    return render_template("contact.html")

app.run(port=5000)

