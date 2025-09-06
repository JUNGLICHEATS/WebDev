# WebDev - Neural Ninja Authentication System

A modern, AI-powered authentication system built with React + Tailwind CSS frontend and FastAPI backend, designed for easy deployment on Vercel and Railway.

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS (deployed on Vercel)
- **Backend**: FastAPI + Python + MongoDB (deployed on Railway)
- **Authentication**: JWT tokens, OTP verification, Google OAuth
- **Development**: Single repository, split deployment

## 📁 Project Structure

```
WebDev/
├── frontend/                  # React + Tailwind CSS app (Vercel deployment)
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── pages/            # Page components
│   │   ├── contexts/         # React contexts (Auth, Toast)
│   │   ├── services/         # API services
│   │   ├── types/            # TypeScript type definitions
│   │   └── utils/            # Utility functions
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── backend/                   # FastAPI app (Railway deployment)
│   ├── main.py               # Main FastAPI application
│   ├── requirements.txt
│   ├── railway.json
│   └── env.example
├── package.json              # Root package for development
├── start.py                  # Local development script
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- MongoDB (local or cloud)
- Git

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/WebDev.git
   cd WebDev
   npm run setup
   ```

2. **Set up environment variables**:
   ```bash
   # Backend environment
   cp backend/env.example backend/.env
   # Edit backend/.env with your MongoDB URL and other settings
   
   # Frontend environment
   cp frontend/.env.example frontend/.env
   # Edit frontend/.env with your API URL
   ```

3. **Start development servers**:
   ```bash
   npm run dev
   # or
   python start.py
   ```

This will start both servers:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## 🌐 Deployment

### Frontend (Vercel)

1. Connect Vercel to your GitHub repository
2. Set Root Directory to `frontend`
3. Deploy automatically on every push

### Backend (Railway)

1. Connect Railway to your GitHub repository
2. Set Root Directory to `backend`
3. Deploy automatically on every push

### Environment Variables

**Frontend (Vercel)**:
- `VITE_API_URL`: Your Railway backend URL

**Backend (Railway)**:
- `MONGODB_URL`: Your MongoDB connection string
- `SECRET_KEY`: JWT secret key
- `EMAIL_ADDRESS`: SMTP email address
- `EMAIL_PASSWORD`: SMTP email password
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret

## 🎨 Features

### Frontend (React + Tailwind CSS)
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Authentication Pages**: Sign in, sign up, OTP verification
- **Dashboard**: User dashboard with stats and activity
- **Context Management**: React contexts for auth and notifications
- **TypeScript**: Full type safety throughout the application
- **Responsive Design**: Mobile-first approach

### Backend (FastAPI)
- **JWT Authentication**: Secure token-based authentication
- **OTP Verification**: Email-based OTP verification system
- **Google OAuth**: Social login with Google
- **MongoDB Integration**: User and OTP data storage
- **Email Service**: SMTP and AWS SES support
- **API Documentation**: Automatic OpenAPI/Swagger docs

## 🔧 Development Commands

```bash
# Install dependencies
npm run setup

# Start both servers
npm run dev

# Start individual servers
npm run start:frontend
npm run start:backend

# Build frontend
npm run build:frontend
```

## 📱 Pages

- **Home** (`/`): Landing page with features and stats
- **Sign In** (`/signin`): User authentication
- **Sign Up** (`/signup`): User registration
- **OTP Verification** (`/verify-otp`): Email verification
- **Dashboard** (`/dashboard`): User dashboard (protected)

## 🛠️ Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Python, MongoDB, Motor
- **Authentication**: JWT, OTP, Google OAuth
- **Deployment**: Vercel (frontend), Railway (backend)
- **Development**: Hot reload, TypeScript, ESLint

## 🔐 Security Features

- JWT token authentication
- Email OTP verification
- Password strength validation
- Google OAuth integration
- CORS protection
- Input validation and sanitization

## 📄 License

MIT License - see LICENSE file for details