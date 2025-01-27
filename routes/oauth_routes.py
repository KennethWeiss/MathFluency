from flask import Blueprint, redirect, url_for, flash, current_app, session, request
from flask_login import current_user, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
import requests
from models.user import User
from models.oauth import OAuth
from app import db, logger
import os
import json

# Create blueprint for OAuth routes
oauth_bp = Blueprint('oauth', __name__, url_prefix='/oauth')

# Get OAuth credentials
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except Exception as e:
        logger.error(f"Error fetching Google provider config: {str(e)}")
        return None

@oauth_bp.route("/google")
def google_login():
    # Log the attempt
    logger.info("Starting Google OAuth login process")
    
    if not current_user.is_anonymous:
        return redirect(url_for("main.home"))

    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        flash("Error connecting to Google.", category="error")
        return redirect(url_for("main.home"))
        
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@oauth_bp.route("/google/callback")
def google_callback():
    # Get authorization code Google sent back
    code = request.args.get("code")
    if not code:
        flash("Failed to log in with Google.", category="error")
        return redirect(url_for("main.home"))

    try:
        # Find out what URL to hit to get tokens
        google_provider_cfg = get_google_provider_cfg()
        if not google_provider_cfg:
            flash("Error connecting to Google.", category="error")
            return redirect(url_for("main.home"))
            
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepare and send a request to get tokens
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
        )
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))
        
        # Now that we have tokens, let's get the user's info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        if userinfo_response.json().get("email_verified"):
            google_id = userinfo_response.json()["sub"]
            email = userinfo_response.json()["email"]
            picture = userinfo_response.json().get("picture")
            first_name = userinfo_response.json().get("given_name")
            last_name = userinfo_response.json().get("family_name")

            # Find existing user or create a new one
            user = User.query.filter_by(google_id=google_id).first()
            if not user:
                user = User.query.filter_by(email=email).first()
                if not user:
                    # Create a new user
                    user = User(
                        username=email.split('@')[0],
                        email=email,
                        google_id=google_id,
                        first_name=first_name,
                        last_name=last_name,
                        avatar_url=picture
                    )
                    db.session.add(user)
                else:
                    # Update existing user with Google info
                    user.google_id = google_id
                    user.avatar_url = picture
                    user.first_name = first_name
                    user.last_name = last_name

            db.session.commit()
            login_user(user)
            flash("Successfully signed in with Google.", category="success")
            return redirect(url_for("main.home"))
        else:
            flash("Google account not verified.", category="error")
            return redirect(url_for("main.home"))

    except Exception as e:
        logger.error(f"Error during Google OAuth: {str(e)}")
        flash("Failed to log in with Google.", category="error")
        return redirect(url_for("main.home"))

@oauth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", category="success")
    return redirect(url_for("main.home"))