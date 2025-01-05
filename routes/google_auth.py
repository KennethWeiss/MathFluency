from flask import Blueprint, session, redirect, request, url_for, flash
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask_login import login_user, current_user
from models.user import User, db
import os
import json

google_auth_bp = Blueprint('google_auth', __name__, url_prefix='/oauth/google')

# Configure Google OAuth2 credentials
CLIENT_SECRETS = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "project_id": "mathfluency-410706",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [
            "http://localhost:5001/oauth/google/callback",
            "https://mathfluency.onrender.com/oauth/google/callback"
        ],
        "javascript_origins": [
            "http://localhost:5001",
            "https://mathfluency.onrender.com"
        ]
    }
}

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_redirect_uri():
    """Get the appropriate redirect URI based on environment"""
    if os.environ.get('RENDER'):
        return "https://mathfluency.onrender.com/oauth/google/callback"
    return "http://localhost:5001/oauth/google/callback"  # Must match exactly what's in Google Console

@google_auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    redirect_uri = get_redirect_uri()
    print(f"Debug - Using redirect URI: {redirect_uri}")
    
    # Create flow instance to manage OAuth 2.0 Authorization Grant Flow
    flow = Flow.from_client_config(
        CLIENT_SECRETS,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Generate URL for request to Google's OAuth 2.0 server
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    # Store state in session
    session['oauth_state'] = state
    print(f"Debug - Stored state in session: {state}")
    
    return redirect(authorization_url)

@google_auth_bp.route('/callback')
def callback():
    try:
        print(f"Debug - Request URL: {request.url}")
        print(f"Debug - Session state: {session.get('oauth_state')}")
        print(f"Debug - Query Params: {request.args}")
        
        # Check if there's an error in the callback
        if 'error' in request.args:
            error = request.args.get('error')
            error_description = request.args.get('error_description', 'No description provided')
            print(f"OAuth Error: {error} - {error_description}")
            flash(f"Google login failed: {error_description}", 'error')
            return redirect(url_for('auth.login'))
        
        # Verify state matches to prevent CSRF attacks
        if 'oauth_state' not in session:
            print("Error: No state in session")
            flash('Session expired. Please try again.', 'error')
            return redirect(url_for('auth.login'))
            
        if 'state' not in request.args or request.args['state'] != session['oauth_state']:
            print(f"State mismatch. Session: {session.get('oauth_state')}, Request: {request.args.get('state')}")
            flash('Invalid state parameter. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        flow = Flow.from_client_config(
            CLIENT_SECRETS,
            scopes=SCOPES,
            state=session['oauth_state'],
            redirect_uri=get_redirect_uri()
        )
        
        try:
            flow.fetch_token(authorization_response=request.url)
        except Exception as e:
            print(f"Token fetch error: {str(e)}")
            flash('Failed to get token from Google. Please try again.', 'error')
            return redirect(url_for('auth.login'))
        
        credentials = flow.credentials

        # Store credentials in session
        session['credentials'] = credentials_to_dict(credentials)

        # Get user info from Google
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()

        # Check if user exists in database
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Create new user
            user = User(
                username=user_info['email'].split('@')[0],  # Use email prefix as username
                email=user_info['email'],
                google_id=user_info['id']
            )
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully!', 'success')
        else:
            # Update existing user's Google ID if not set
            if not user.google_id:
                user.google_id = user_info['id']
                db.session.commit()

        # Log in the user
        login_user(user)
        flash('Logged in successfully!', 'success')
        
        # Redirect to welcome page
        return redirect(url_for('main.welcome'))

    except Exception as e:
        print(f"Google OAuth Error: {str(e)}")
        flash('Failed to log in with Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@google_auth_bp.route('/debug')
def debug():
    """Debug endpoint to check Google Auth configuration"""
    debug_info = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_id_in_secrets': CLIENT_SECRETS['web']['client_id'],
        'client_secret_exists': bool(os.environ.get('GOOGLE_CLIENT_SECRET')),
        'session_state': session.get('oauth_state', 'Not set'),
        'credentials': session.get('credentials', 'Not set'),
        'current_url': request.url,
        'callback_url': url_for('google_auth.callback', _external=True)
    }
    return str(debug_info)
