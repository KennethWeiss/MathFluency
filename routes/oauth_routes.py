from flask import Blueprint, redirect, url_for, flash, current_app, session, request
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError, TokenExpiredError
from models.user import User
from models.oauth import OAuth
from app import db, logger
import os
import logging
from functools import partial

# Enable Flask-Dance debug logging
logging.basicConfig(level=logging.DEBUG)

class CustomSQLAlchemyStorage(SQLAlchemyStorage):
    def get(self, *args, **kwargs):
        return super().get(*args, user=current_user._get_current_object(), **kwargs)

# Create blueprint for OAuth routes
oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

# Get OAuth credentials
client_id = os.environ.get("GOOGLE_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

logger.debug("OAuth Configuration:")
logger.debug(f"GOOGLE_CLIENT_ID exists: {client_id is not None}")
logger.debug(f"GOOGLE_CLIENT_SECRET exists: {client_secret is not None}")
logger.debug(f"GOOGLE_CLIENT_ID length: {len(client_id) if client_id else 0}")
logger.debug(f"GOOGLE_CLIENT_SECRET length: {len(client_secret) if client_secret else 0}")

# Create blueprint for Google OAuth
blueprint = make_google_blueprint(
    client_id=client_id,
    client_secret=client_secret,
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    storage=CustomSQLAlchemyStorage(
        OAuth,
        db.session,
        user_required=False
    ),
    redirect_url=None,
    reprompt_consent=True
)

oauth_bp.register_blueprint(blueprint, url_prefix="/login")

@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    logger.debug("Google OAuth callback received")
    if not token:
        logger.warning("Failed to log in with Google: no token received")
        flash("Failed to log in with Google.", category="error")
        return False

    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.warning("Failed to fetch user info from Google")
            flash("Failed to fetch user info from Google.", category="error")
            return False

        google_info = resp.json()
        google_user_id = str(google_info["id"])
        logger.debug(f"Google user info received: {google_info}")

        # Find this OAuth token in the database, or create it
        query = OAuth.query.filter_by(
            provider=blueprint.name,
            provider_user_id=google_user_id,
        )
        try:
            oauth = query.one()
        except Exception:
            oauth = OAuth(
                provider=blueprint.name,
                provider_user_id=google_user_id,
                token=token,
            )

        if oauth.user:
            logger.debug(f"Existing user found: {oauth.user}")
            login_user(oauth.user)
            flash("Successfully signed in with Google.", category="success")
            return False

        # No user found, so create a new user
        user = User(
            username=google_info["email"].split("@")[0],  # Use email prefix as username
            email=google_info["email"],
            google_id=google_user_id,
            first_name=google_info.get("given_name"),
            last_name=google_info.get("family_name"),
            avatar_url=google_info.get("picture")
        )
        oauth.user = user
        db.session.add_all([user, oauth])
        db.session.commit()
        login_user(user)
        flash("Successfully signed in with Google.", category="success")
        return False

    except (InvalidGrantError, TokenExpiredError) as e:
        logger.error(f"OAuth error: {str(e)}")
        flash("Failed to log in with Google.", category="error")
        return False

@oauth_bp.route("/google")
def google_login():
    if not current_user.is_anonymous:
        return redirect(url_for("index"))
    return redirect(url_for("google.login"))

@oauth_bp.route("/google/authorized")
def google_authorized():
    if not google.authorized:
        flash("Failed to log in with Google.", category="error")
        return redirect(url_for("index"))
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if resp.ok:
            return redirect(url_for("index"))
        else:
            flash("Failed to fetch user info from Google.", category="error")
            return redirect(url_for("index"))
    except (InvalidGrantError, TokenExpiredError):
        flash("Failed to log in with Google.", category="error")
        return redirect(url_for("index"))

@oauth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", category="success")
    return redirect(url_for("index"))