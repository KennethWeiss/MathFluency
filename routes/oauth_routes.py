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

# Enable Flask-Dance debug logging
logging.basicConfig(level=logging.DEBUG)

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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
    storage=SQLAlchemyStorage(
        OAuth,
        db.session,
        user=current_user,
        user_required=False
    ),
    redirect_url=None,
    reprompt_consent=True  # Show consent screen to see what's blocked
)

@oauth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    logger.debug("Accessing /oauth/google/login route")
    logger.debug("Environment variables check:")
    logger.debug(f"GOOGLE_CLIENT_ID exists: {os.environ.get('GOOGLE_CLIENT_ID') is not None}")
    logger.debug(f"GOOGLE_CLIENT_SECRET exists: {os.environ.get('GOOGLE_CLIENT_SECRET') is not None}")
    logger.debug(f"Blueprint client_id exists: {blueprint.client_id is not None}")
    logger.debug(f"Blueprint client_secret exists: {blueprint.client_secret is not None}")

    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to welcome page")
        return redirect(url_for('main.welcome'))
    
    # Store the next URL in session if provided
    next_url = request.args.get('next')
    if next_url:
        session['next_url'] = next_url
    
    logger.debug("Starting Google OAuth flow")
    return redirect(url_for('google.login'))

@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    """Handle successful OAuth login"""
    logger.debug("OAuth authorized callback triggered")
    if not token:
        logger.warning("Failed to log in with Google: no token received")
        flash("Failed to log in with Google.", category="error")
        return False

    try:
        # Log token information
        logger.debug("Token received:")
        logger.debug(f"Scopes granted: {token.get('scope', [])}")
        
        # Try to get user info
        logger.debug("Attempting to fetch user info...")
        resp = blueprint.session.get("/oauth2/v2/userinfo")
        logger.debug(f"User info response status: {resp.status_code}")
        logger.debug(f"User info response: {resp.text if resp.ok else 'Failed'}")

        if not resp.ok:
            logger.error(f"Failed to fetch user info: {resp.text}")
            return False

        google_info = resp.json()
        google_user_id = google_info["id"]
        
        # Find or create user
        user = User.query.filter_by(google_id=google_user_id).first()
        if user:
            logger.debug(f"Found existing user: {user.email}")
        else:
            logger.debug("Creating new user")
            user = User(
                username=google_info.get("name", ""),
                email=google_info["email"],
                google_id=google_user_id,
                avatar_url=google_info.get("picture"),
                first_name=google_info.get("given_name"),
                last_name=google_info.get("family_name"),
                is_teacher=False  # All new users start as students
            )
            db.session.add(user)
            db.session.commit()

        # Log in the user
        login_user(user)
        flash("Successfully logged in with Google.", category="success")
        
        return False  # Let Flask-Dance handle redirect

    except Exception as e:
        logger.exception("Error in OAuth callback")
        flash("An error occurred during login.", category="error")
        return False

@oauth_bp.route('/authorized/google')
def google_authorized():
    """Handle the Google OAuth callback"""
    if not google.authorized:
        logger.warning("Google OAuth not authorized in callback")
        flash("Failed to log in with Google.", category="error")
        return redirect(url_for('auth.login'))

    try:
        # Get user info to confirm authorization worked
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            logger.error(f"Failed to get user info in callback: {resp.text}")
            flash("Failed to get user info from Google.", category="error")
            return redirect(url_for('auth.login'))
        
        # Get the next URL from session if it exists
        next_url = session.pop('next_url', None)
        if next_url:
            logger.debug(f"Redirecting to next_url: {next_url}")
            return redirect(next_url)
        
        logger.debug("Redirecting to welcome page")
        return redirect(url_for('main.welcome'))

    except Exception as e:
        logger.exception("Error in google_authorized callback")
        flash("An error occurred during login. Please try again.", category="error")
        return redirect(url_for('auth.login'))

@oauth_bp.route('/logout')
def logout():
    """Log out the user"""
    logout_user()
    # Clear the OAuth token
    token = blueprint.token
    if token:
        del blueprint.token
    return redirect(url_for('auth.login'))