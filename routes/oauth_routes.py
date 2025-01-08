import os
from flask import Blueprint, redirect, url_for, flash, current_app, session
from flask_login import current_user, login_user, logout_user
from flask_dance.contrib.google import make_google_blueprint, google
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError, InvalidGrantError
from models.user import User
from app import db
import logging

logger = logging.getLogger(__name__)
oauth_bp = Blueprint('oauth', __name__)

# Enable Flask-Dance debug logging
logging.basicConfig(level=logging.DEBUG)

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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
    storage=None,
    redirect_url=None,
    reprompt_consent=True  # Show consent screen to see what's blocked
)

def get_google_user_info():
    """Get user info from Google OAuth."""
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.error("Failed to get user info from Google")
            return None
        return resp.json()
    except (TokenExpiredError, InvalidGrantError) as e:
        logger.error(f"OAuth error: {str(e)}")
        return None

@oauth_bp.route("/oauth/google")
def google_login():
    """Initiate Google OAuth login."""
    if not google.authorized:
        return redirect(url_for("google.login"))
    return redirect(url_for("oauth.google_authorized"))

@oauth_bp.route("/oauth/authorized/google/authorized")
def google_authorized():
    """Handle Google OAuth callback."""
    if not google.authorized:
        flash("Failed to log in with Google.", "error")
        return redirect(url_for("auth.login"))

    google_info = get_google_user_info()
    if not google_info:
        flash("Failed to get Google user info.", "error")
        return redirect(url_for("auth.login"))

    google_user_id = google_info["id"]
    email = google_info["email"]
    
    # Find or create user
    user = User.query.filter_by(google_id=google_user_id).first()
    if user:
        # Update existing user
        user.avatar_url = google_info.get("picture")
        user.first_name = google_info.get("given_name")
        user.last_name = google_info.get("family_name")
        
        # Check if user should be admin (based on email)
        admin_emails = current_app.config.get('ADMIN_EMAILS', [])
        if email in admin_emails and not user.is_admin:
            user.is_admin = True
            db.session.commit()
            login_user(user)  # Refresh session with admin status
    else:
        # Create new user
        username = email.split('@')[0]  # Use email prefix as username
        user = User(
            username=username,
            email=email,
            google_id=google_user_id,
            avatar_url=google_info.get("picture"),
            first_name=google_info.get("given_name"),
            last_name=google_info.get("family_name")
        )
        if email in current_app.config.get('ADMIN_EMAILS', []):
            user.is_admin = True
        db.session.add(user)
        db.session.commit()

    login_user(user)
    next_url = session.pop('next', None)
    return redirect(next_url or url_for('main.welcome'))

@oauth_bp.route("/oauth/logout")
def logout():
    """Handle logout."""
    logout_user()
    return redirect(url_for('auth.login'))