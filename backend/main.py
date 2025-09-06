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
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/webdev")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# AWS SES configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Database connection
client = None
db = None
users_collection = None
otp_collection = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# OAuth setup
oauth = OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid_configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OTPVerification(BaseModel):
    email: EmailStr
    otp: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    is_verified: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Email sending function
async def send_otp_email(email: str, otp: str):
    try:
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            # Use AWS SES
            ses_client = boto3.client(
                'ses',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
            
            ses_client.send_email(
                Source=SMTP_USERNAME or "noreply@yourdomain.com",
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': 'Email Verification Code'},
                    'Body': {
                        'Text': {'Data': f'Your verification code is: {otp}'},
                        'Html': {'Data': f'<h1>Email Verification</h1><p>Your verification code is: <strong>{otp}</strong></p>'}
                    }
                }
            )
        elif SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD:
            # Use SMTP
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = "Email Verification Code"
            
            body = f"Your verification code is: {otp}"
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(SMTP_USERNAME, email, text)
            server.quit()
        else:
            # Log to console for development
            print(f"OTP for {email}: {otp}")
    except Exception as e:
        print(f"Error sending email: {e}")
        # For development, just log the OTP
        print(f"OTP for {email}: {otp}")

# Database initialization
@app.on_event("startup")
async def startup_db_client():
    global client, db, users_collection, otp_collection
    
    try:
        # MongoDB connection with TLS options
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URL,
            tlsCAFile=certifi.where()
        )
        db = client.webdev
        users_collection = db.users
        otp_collection = db.otps
        
        # Test the connection
        await client.admin.command('ping')
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        # Continue without database for development
        client = None
        db = None
        users_collection = None
        otp_collection = None

# API Routes
@app.get("/")
async def root():
    return {"message": "WebDev Authentication API", "status": "running"}

@app.post("/api/signup", response_model=dict)
async def signup(user_data: UserCreate):
    if not users_collection:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Generate OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Store user
    user_doc = {
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password,
        "is_verified": False,
        "created_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Store OTP
    otp_doc = {
        "email": user_data.email,
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    await otp_collection.insert_one(otp_doc)
    
    # Send OTP email
    await send_otp_email(user_data.email, otp)
    
    return {
        "success": True,
        "message": "User created successfully. Please check your email for verification code.",
        "user_id": user_id
    }

@app.post("/api/signin", response_model=TokenResponse)
async def signin(login_data: UserLogin):
    if not users_collection:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Find user
    user = await users_collection.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not pwd_context.verify(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user is verified
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=400, 
            detail="Please verify your email before signing in",
            headers={"requires_otp": "true"}
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["_id"])}, 
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user["_id"]),
            name=user["name"],
            email=user["email"],
            is_verified=user.get("is_verified", False),
            created_at=user["created_at"]
        )
    )

@app.post("/api/verify-otp", response_model=dict)
async def verify_otp(otp_data: OTPVerification):
    if not otp_collection or not users_collection:
        raise HTTPException(status_code=500, detail="Database not available")
    
    # Find OTP
    otp_doc = await otp_collection.find_one({
        "email": otp_data.email,
        "otp": otp_data.otp,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Update user as verified
    await users_collection.update_one(
        {"email": otp_data.email},
        {"$set": {"is_verified": True}}
    )
    
    # Delete used OTP
    await otp_collection.delete_one({"_id": otp_doc["_id"]})
    
    return {"success": True, "message": "Email verified successfully"}

@app.post("/api/resend-otp", response_model=dict)
async def resend_otp(email_data: dict):
    if not otp_collection or not users_collection:
        raise HTTPException(status_code=500, detail="Database not available")
    
    email = email_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Check if user exists
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new OTP
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Store new OTP
    otp_doc = {
        "email": email,
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    await otp_collection.insert_one(otp_doc)
    
    # Send OTP email
    await send_otp_email(email, otp)
    
    return {"success": True, "message": "OTP sent successfully"}

# Google OAuth routes
@app.get("/api/auth/google")
async def google_auth():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    redirect_uri = f"{BASE_URL}/api/auth/google/callback"
    return await oauth.google.authorize_redirect(redirect_uri)

@app.get("/api/auth/google/callback")
async def google_callback(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Could not get user info from Google")
        
        email = user_info.get("email")
        name = user_info.get("name")
        google_id = user_info.get("sub")
        
        if not email or not name or not google_id:
            raise HTTPException(status_code=400, detail="Incomplete user info from Google")
        
        if not users_collection:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if user exists
        existing_user = await users_collection.find_one({"email": email})
        
        if existing_user:
            # Update Google ID if not set
            if not existing_user.get("google_id"):
                await users_collection.update_one(
                    {"_id": existing_user["_id"]},
                    {"$set": {"google_id": google_id, "is_verified": True}}
                )
            user_id = str(existing_user["_id"])
        else:
            # Create new user
            user_doc = {
                "name": name,
                "email": email,
                "google_id": google_id,
                "is_verified": True,
                "created_at": datetime.utcnow()
            }
            result = await users_collection.insert_one(user_doc)
            user_id = str(result.inserted_id)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, 
            expires_delta=access_token_expires
        )
        
        # Redirect to frontend with token
        frontend_url = f"{BASE_URL.replace(':8000', ':3000')}/dashboard?token={access_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")

# Protected routes
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not users_collection:
        raise HTTPException(status_code=500, detail="Database not available")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await users_collection.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@app.get("/api/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
        is_verified=current_user.get("is_verified", False),
        created_at=current_user["created_at"]
    )

@app.post("/api/logout")
async def logout():
    # In a production app, you might want to blacklist the token
    return {"success": True, "message": "Logged out successfully"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Debug endpoint for OAuth configuration
@app.get("/api/debug/oauth")
async def debug_oauth():
    return {
        "google_client_id": bool(GOOGLE_CLIENT_ID),
        "google_client_secret": bool(GOOGLE_CLIENT_SECRET),
        "base_url": BASE_URL,
    }

# Database initialization on startup
@app.on_event("startup")
async def create_indexes():
    if not users_collection or not otp_collection:
        return
    
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
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
