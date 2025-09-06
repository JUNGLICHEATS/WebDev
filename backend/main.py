Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Usage: uvicorn [OPTIONS] APP
Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Usage: uvicorn [OPTIONS] APP
Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Usage: uvicorn [OPTIONS] APP
Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Usage: uvicorn [OPTIONS] APP
Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Usage: uvicorn [OPTIONS] APP
Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
Usage: uvicorn [OPTIONS] APP
Try 'uvicorn --help' for help.
Error: Invalid value for '--port': '$PORT' is not a valid integer.
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import motor.motor_asyncio
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import os
from typing import Optional
import httpx
from authlib.integrations.starlette_client import OAuth
import boto3
from dotenv import load_dotenv
import certifi
import logging
import re

load_dotenv()
app = FastAPI(title="Authentication API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://healthcheck.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
# Frontend directory (one level up from backend)
frontend_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# Add session middleware for OAuth state handling
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "auth_db")

# Optional TLS configuration via env flags
USE_CERTIFI_CA = os.getenv("MONGODB_USE_CERTIFI", "1") not in {"0", "false", "False"}
TLS_INSECURE = os.getenv("MONGODB_TLS_INSECURE", "0") in {"1", "true", "True"}
SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "30000"))

# Email configuration
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp")  # 'smtp' or 'ses'
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SES_REGION = os.getenv("SES_REGION", "us-east-1")

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Logger
logger = logging.getLogger("uvicorn.error")

# Initialize MongoDB
mongo_kwargs = {"serverSelectionTimeoutMS": SERVER_SELECTION_TIMEOUT_MS}
# Enable TLS and provide CA bundle for Atlas hosts by default
if ".mongodb.net" in MONGODB_URL or MONGODB_URL.startswith("mongodb+srv://"):
    mongo_kwargs["tls"] = True
    if USE_CERTIFI_CA:
        mongo_kwargs["tlsCAFile"] = certifi.where()
if TLS_INSECURE:
    mongo_kwargs["tlsAllowInvalidCertificates"] = True

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL, **mongo_kwargs)
database = client[DATABASE_NAME]
users_collection = database.get_collection("users")
otp_collection = database.get_collection("otps")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Pydantic models
class UserSignUp(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str

class ResendOTP(BaseModel):
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    is_verified: bool

# Utility Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

async def send_otp_email(email: str, otp: str) -> bool:
    try:
        subject = "Your Neural Ninja Verification Code"
        body = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden;">
                <!-- Header with Logo -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <div style="background: #ffffff; width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                        <div style="font-size: 24px; font-weight: bold; color: #667eea;">NN</div>
                    </div>
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 300;">Neural Ninja</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 14px;">Secure Email Verification</p>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 40px 30px;">
                    <h2 style="color: #333; margin: 0 0 20px 0; font-size: 24px; text-align: center;">Email Verification Required</h2>
                    
                    <p style="color: #666; font-size: 16px; line-height: 1.6; margin: 0 0 25px 0;">
                        Hello! We've received a request to verify your email address. Please use the verification code below to complete the process.
                    </p>
                    
                    <!-- OTP Code Box -->
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 30px; border-radius: 15px; text-align: center; margin: 30px 0; border: 2px dashed #667eea;">
                        <p style="margin: 0 0 10px 0; color: #666; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Your Verification Code</p>
                        <h1 style="color: #667eea; font-size: 36px; letter-spacing: 8px; margin: 0; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);">{otp}</h1>
                    </div>
                    
                    <!-- Security Warning -->
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 25px 0;">
                        <div style="display: flex; align-items: flex-start;">
                            <div style="color: #856404; font-size: 20px; margin-right: 15px; font-weight: bold;">⚠️</div>
                            <div>
                                <h3 style="color: #856404; margin: 0 0 10px 0; font-size: 16px; font-weight: bold;">Security Warning</h3>
                                <ul style="color: #856404; margin: 0; padding-left: 0; list-style: none; font-size: 14px; line-height: 1.6;">
                                    <li style="margin-bottom: 8px;">🔒 <strong>Never share this code</strong> with anyone, including Neural Ninja staff</li>
                                    <li style="margin-bottom: 8px;">📱 Only enter this code on the official Neural Ninja website/app</li>
                                    <li style="margin-bottom: 8px;">⏰ This code expires in <strong>10 minutes</strong></li>
                                    <li>🚨 If you didn't request this verification, secure your account immediately</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <p style="color: #999; font-size: 14px; line-height: 1.6; margin: 25px 0 0 0; text-align: center;">
                        If you didn't request this verification code, please ignore this email or contact our support team if you have concerns about your account security.
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="background: #f8f9fa; padding: 25px 30px; border-top: 1px solid #e9ecef;">
                    <div style="text-align: center;">
                        <p style="color: #6c757d; margin: 0 0 10px 0; font-size: 12px;">
                            © 2025 Neural Ninja Team. All rights reserved.
                        </p>
                        <p style="color: #6c757d; margin: 0; font-size: 12px;">
                            This is an automated message. Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        if EMAIL_PROVIDER.lower() == 'ses':
            ses = boto3.client('ses', region_name=SES_REGION)
            ses.send_email(
                Source=EMAIL_ADDRESS,
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Html': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )
            return True

        # Default SMTP
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Find user with case-insensitive email matching
    user = await users_collection.find_one({"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}})
    if user is None:
        raise credentials_exception
    return user

# API Routes
@app.post("/api/signup")
async def signup(user_data: UserSignUp):
    try:
        # Normalize email to lowercase for consistent checking
        normalized_email = user_data.email.lower()
        
        # Check if user already exists (case-insensitive)
        existing_user = await users_collection.find_one({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
        if existing_user:
            # Check if user is already verified
            if existing_user.get("is_verified"):
                raise HTTPException(
                    status_code=400,
                    detail="An account with this email already exists. Please sign in instead."
                )
            else:
                # User exists but not verified - offer to resend OTP
                raise HTTPException(
                    status_code=400,
                    detail="An account with this email already exists but is not verified. Please check your email for verification code or use the resend option."
                )

        # Create new user with normalized email
        hashed_password = hash_password(user_data.password)
        user_doc = {
            "name": user_data.name,
            "email": normalized_email,  # Store normalized email
            "password_hash": hashed_password,
            "is_verified": False,
            "created_at": datetime.utcnow()
        }

        result = await users_collection.insert_one(user_doc)
        
        # Generate and send OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        otp_doc = {
            "email": normalized_email,
            "code": otp_code,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_used": False
        }

        # Delete any existing OTP for this email
        await otp_collection.delete_many({"email": normalized_email})
        await otp_collection.insert_one(otp_doc)

        # Send OTP email
        email_sent = await send_otp_email(normalized_email, otp_code)
        
        if not email_sent:
            # For demo purposes, return the OTP in response
            return {
                "success": True,
                "message": "Account created successfully. Check your email for verification code.",
                "demo_otp": otp_code  # Remove this in production
            }

        return {
            "success": True,
            "message": "Account created successfully. Check your email for verification code."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/signin")
async def signin(user_data: UserSignIn):
    try:
        # Normalize email to lowercase for consistent checking
        normalized_email = user_data.email.lower()
        
        # Find user (case-insensitive)
        user = await users_collection.find_one({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
        if not user or not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # Check if user is verified
        if not user["is_verified"]:
            # Generate and send OTP
            otp_code = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            otp_doc = {
                "email": normalized_email,
                "code": otp_code,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_used": False
            }

            await otp_collection.delete_many({"email": normalized_email})
            await otp_collection.insert_one(otp_doc)

            email_sent = await send_otp_email(normalized_email, otp_code)
            
            return {
                "success": True,
                "requires_otp": True,
                "message": "Please verify your email to continue.",
                "demo_otp": otp_code if not email_sent else None  # Remove in production
            }

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )

        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Signed in successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/verify-otp")
async def verify_otp(otp_data: OTPVerification):
    try:
        # Normalize email to lowercase for consistent checking
        normalized_email = otp_data.email.lower()
        
        # Find valid OTP
        otp_record = await otp_collection.find_one({
            "email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"},
            "code": otp_data.otp,
            "is_used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if not otp_record:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired verification code"
            )

        # Mark OTP as used
        await otp_collection.update_one(
            {"_id": otp_record["_id"]},
            {"$set": {"is_used": True}}
        )

        # Mark user as verified
        await users_collection.update_one(
            {"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}},
            {"$set": {"is_verified": True}}
        )

        # Get user and create token
        user = await users_collection.find_one({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )

        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Email verified successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/resend-otp")
async def resend_otp(resend_data: ResendOTP):
    try:
        # Normalize email to lowercase for consistent checking
        normalized_email = resend_data.email.lower()
        
        # Check if user exists
        user = await users_collection.find_one({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if user["is_verified"]:
            raise HTTPException(
                status_code=400,
                detail="User is already verified"
            )

        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        otp_doc = {
            "email": normalized_email,
            "code": otp_code,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_used": False
        }

        # Delete existing OTPs and create new one
        await otp_collection.delete_many({"email": normalized_email})
        await otp_collection.insert_one(otp_doc)

        # Send OTP email
        email_sent = await send_otp_email(normalized_email, otp_code)

        return {
            "success": True,
            "message": "Verification code sent successfully",
            "demo_otp": otp_code if not email_sent else None  # Remove in production
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/auth/google")
async def google_auth(request: Request):
    try:
        # Ensure we have a proper base URL
        if not BASE_URL or BASE_URL == "http://localhost:8000":
            # Try to get the actual host from the request
            host = request.headers.get("host", "localhost:8000")
            scheme = request.headers.get("x-forwarded-proto", "http")
            base_url = f"{scheme}://{host}"
        else:
            base_url = BASE_URL
            
        redirect_uri = f"{base_url}/api/auth/google/callback"
        logger.info(f"Starting Google OAuth with redirect URI: {redirect_uri}")
        
        # Use the constructed redirect URI instead of request.url_for
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        logger.error(f"Google OAuth redirect error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth redirect failed: {str(e)}")

@app.get("/api/auth/google/callback")
async def google_auth_callback(request: Request):
    try:
        # Check for OAuth errors in query parameters
        error = request.query_params.get("error")
        if error:
            logger.error(f"OAuth error received: {error}")
            # Redirect to signin page with error
            return RedirectResponse(url=f"/signin.html?error={error}")
        
        token = await oauth.google.authorize_access_token(request)
        if not token:
            # Redirect to signin page with error
            return RedirectResponse(url="/signin.html?error=auth_failed")
        
        # Get user info from Google's userinfo endpoint
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )
            if resp.status_code != 200:
                return RedirectResponse(url="/signin.html?error=userinfo_failed")
            user_info = resp.json()
        
        email = user_info.get("email")
        name = user_info.get("name") or user_info.get("given_name") or "Google User"
        google_id = user_info.get("id")
        
        if not email:
            return RedirectResponse(url="/signin.html?error=no_email")
        
        # Normalize email to lowercase
        normalized_email = email.lower()
        
        # Check if user exists (case-insensitive)
        existing_user = await users_collection.find_one({"email": {"$regex": f"^{re.escape(normalized_email)}$", "$options": "i"}})
        
        if existing_user:
            # Update existing user with Google ID if not present
            if not existing_user.get("google_id"):
                await users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {"$set": {"google_id": google_id, "is_verified": True}}
                )
        else:
            # Create new user with normalized email
            user_doc = {
                "name": name,
                "email": normalized_email,
                "password_hash": None,
                "is_verified": True,
                "google_id": google_id,
                "created_at": datetime.utcnow()
            }
            await users_collection.insert_one(user_doc)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        # Redirect to dashboard with token in URL (for demo purposes)
        # In production, you might want to use a more secure method
        dashboard_url = f"/dashboard.html?token={access_token}&auth=google"
        return RedirectResponse(url=dashboard_url)
        
    except HTTPException:
        # Redirect to signin page with generic error
        return RedirectResponse(url="/signin.html?error=unknown")
    except Exception as e:
        logger.error(f"Google authentication error: {str(e)}")
        return RedirectResponse(url="/signin.html?error=server_error")

@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
        is_verified=current_user["is_verified"]
    )

@app.post("/api/logout")
async def logout():
    # In a production app, you might want to blacklist the token
    return {"success": True, "message": "Logged out successfully"}

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Check if database is connected
        if client:
            # Simple ping to check database connection
            await client.admin.command('ping')
        
        return {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        # Still return healthy even if DB is down for basic health checks
        return {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected",
            "note": "Basic health check passed"
        }

# Debug endpoint for OAuth configuration
@app.get("/api/debug/oauth")
async def debug_oauth():
    return {
        "google_client_id": bool(GOOGLE_CLIENT_ID),
        "google_client_secret": bool(GOOGLE_CLIENT_SECRET),
        "base_url": BASE_URL,
        "oauth_registered": "google" in oauth._clients
    }

# Serve static files and main page
@app.get("/", response_class=HTMLResponse)
async def serve_auth_page():
    # Prefer project's frontend if present
    candidates = [
        os.path.join(frontend_dir, "index.html"),
        os.path.join(frontend_dir, "signin.html"),
        os.path.join(frontend_dir, "signup.html"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return FileResponse(path)
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication System</title>
    </head>
    <body>
        <h1>Authentication System</h1>
        <p>Use the API endpoints or serve your HTML file here.</p>
        <ul>
            <li>POST /api/signup - Create new account</li>
            <li>POST /api/signin - Sign in</li>
            <li>POST /api/verify-otp - Verify OTP</li>
            <li>POST /api/resend-otp - Resend OTP</li>
            <li>GET /api/auth/google - Google OAuth</li>
            <li>GET /api/me - Get current user info</li>
        </ul>
    </body>
    </html>
    """
# Serve frontend static assets at root so relative paths like /styles.css work
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir), name="frontend_root")

# Database initialization
@app.on_event("startup")
async def startup_event():
    # Validate DB connectivity early with a ping for clearer error messages
    try:
        await database.command({"ping": 1})
    except Exception as exc:
        logger.error(
            "Failed to connect to MongoDB. Check your MONGODB_URL and TLS/network settings. "
            "You can set MONGODB_USE_CERTIFI=1 (default) to trust standard CAs or MONGODB_TLS_INSECURE=1 to bypass cert validation temporarily. Error: %s",
            exc,
        )
        raise

    # Create indexes for better performance
    # Clean up any documents that may have google_id explicitly set to None to avoid unique index conflicts
    await users_collection.update_many({"google_id": None}, {"$unset": {"google_id": ""}})

    # Ensure a proper unique index that ignores documents without a valid google_id
    try:
        await users_collection.drop_index("google_id_1")
    except Exception:
        pass
    try:
        await users_collection.drop_index("google_id_unique")
    except Exception:
        pass

    await users_collection.create_index("email", unique=True)
    await users_collection.create_index(
        "google_id",
        name="google_id_unique",
        unique=True,
        partialFilterExpression={"google_id": {"$exists": True, "$type": "string"}}
    )
    await otp_collection.create_index("email")
    await otp_collection.create_index("expires_at", expireAfterSeconds=0)  # TTL index

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    # Bind to both IPv4 and IPv6 for Railway v2 compatibility
    uvicorn.run(app, host="::", port=port, reload=True)
