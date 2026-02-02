# OrderBuddy FastAPI Backend - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.10 or higher
- MongoDB running (or MongoDB Atlas URI)

### Step 1: Install Dependencies
```bash
cd python-backend-demo
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your MongoDB connection
nano .env  # or use any text editor
```

**Required settings:**
```bash
DB_CONN_STRING=mongodb+srv://username:password@cluster/
DB_NAME=order-buddy-v1
```

### Step 3: Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Step 4: Verify Installation
Open your browser to:
- **API Health:** http://localhost:8000/health
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📱 Running with Frontend Apps

### Terminal 1: Start Backend
```bash
cd python-backend-demo
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Start Order App (Mobile)
```bash
cd src/order
npm install  # first time only
npm run dev  # Runs on port 5173
```

### Terminal 3: Start Manage App (Dashboard)
```bash
cd src/manage
npm install  # first time only
npm run dev  # Runs on port 5174
```

---

## 🧪 Quick Test

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test menu endpoint
curl 'http://localhost:8000/restaurant/restaurants/cuppa_co/locations/cuppa_co_main/menus'

# Test authentication
curl -X POST 'http://localhost:8000/login/otp-request' \
  -H 'Content-Type: application/json' \
  -d '{"phoneNumber":"+1234567890"}'
```

---

## 📂 Access the Apps

- **Order App (Customer):** http://localhost:5173/entry/cuppa_co/seattle?name=Cuppa%20Co&originId=table-1
- **Manage App (Dashboard):** http://localhost:5174/cuppa_co/cuppa_co_main/apps/orders
- **API Documentation:** http://localhost:8000/docs

---

## 🔧 Common Issues

### MongoDB Connection Error
```bash
# Check MongoDB is running
mongosh

# Or verify your connection string in .env
DB_CONN_STRING=mongodb+srv://...
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### CORS Errors
Make sure `.env` includes:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
```

---

## 📖 Next Steps

- Read [SUBMISSION_REPORT.md](SUBMISSION_REPORT.md) for complete implementation details
- Read [README.md](README.md) for comprehensive documentation
- Check [API Documentation](http://localhost:8000/docs) for endpoint reference

---

## 🎯 Quick Command Reference

```bash
# Start backend
uvicorn app.main:app --reload

# Start with specific port
uvicorn app.main:app --reload --port 8000

# Start with custom host
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run tests
pytest

# Check logs
tail -f logs/app.log
```

---

**Status:** Production Ready ✅
**Version:** 2.0.0
**Documentation:** See SUBMISSION_REPORT.md for complete details
