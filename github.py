import os
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, redirect, url_for, jsonify
from flask_dance.contrib.github import make_github_blueprint, github
from flask_sqlalchemy import SQLAlchemy
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend

db = SQLAlchemy()
class OAuth(OAuthConsumerMixin, db.Model):
    pass


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersekrit")
app.config["GITHUB_OAUTH_CLIENT_ID"] = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
app.config["GITHUB_OAUTH_CLIENT_SECRET"] = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["BASE_DIR"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///{}'.format(os.path.join(app.config["BASE_DIR"], 'dance.db'))

db.init_app(app)
with app.test_request_context():
    # hack to automatically create all the tables
    db.create_all()

github_bp = make_github_blueprint()
github_bp.backend = SQLAlchemyBackend(OAuth, db.session)

app.register_blueprint(github_bp, url_prefix="/login")

@app.route("/")
def index():
    if not github.authorized:
        return redirect(url_for("github.login"))
    resp = github.get("/user")
    assert resp.ok
    return "You are @{login} on GitHub".format(login=resp.json()["login"])


@app.route("/check")
def check_github():
    resp = {
        'access_token': github.access_token,
        'token': github.token
    }
    return jsonify(resp)



if __name__ == "__main__":
    app.run()
