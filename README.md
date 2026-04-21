# AquaAlert

> **Smart Early Warning System for Water Borne Diseases**

<h3>Live : https://aquaalert-1.onrender.com/ </h3>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript"/>
</p>

---

## Problem Statement

**Water borne diseases** like cholera, typhoid, and dengue affect millions globally, especially in developing regions. Key challenges include:

- **Delayed Detection**: Hazards like stagnant water, open sewage, and contaminated sources go unreported for days
- **Lack of Evidence**: Reports without geo-tagged proof are hard to verify and prioritize
- **Fragmented Response**: No unified system connecting citizens, supervisors, and field workers
- **No Accountability**: Difficult to track if reported issues were actually resolved

---

## Solution

**AquaAlert** is a comprehensive early warning platform that transforms citizen observations into verified, accountable action through:

1. **Evidence-First Reporting** — GPS-locked photos with accuracy validation
2. **Intelligent Clustering** — Groups nearby reports into hotspots for prioritized response
3. **Role-Based Dashboards** — Dedicated portals for citizens, supervisors, and field workers
4. **QR-Based Navigation** — Quick dispatch with scannable location codes
5. **Proof-Based Closure** — Geo-stamped completion photos for audit trails

---

## Key Features

### Geo-Tagged Reports
- GPS accuracy checks (rejects if accuracy > 100m)
- Automatic reverse geocoding for district/city
- Photo evidence with metadata preservation

### Hotspot Detection & Clustering
- Proximity-based clustering algorithm groups nearby reports
- Dynamic severity escalation based on community votes
- Priority scoring: `report_count × severity_weight`

### Community Validation
- Nearby users can upvote/downvote reports
- Validation affects cluster severity (escalation rules)
- Prevents false reports through crowd verification

### QR Navigation System
- Auto-generated QR codes for each report
- One-scan navigation to exact location
- Speeds up field worker dispatch

### Role-Based Access Control
- **Users**: Report hazards, track status, validate nearby reports
- **Supervisors**: Accept/reject reports, assign workers, verify completion
- **Workers**: View assignments, navigate via QR, upload completion proof

### Real-Time Dashboard
- Live report status tracking
- Cluster visualization on map
- Worker availability management

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Landing    │  │   Auth UI    │  │  Dashboards  │          │
│  │    Page      │  │ Login/Signup │  │ User/Sup/Wkr │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API ROUTES                            │   │
│  │  /auth  │  /reports  │  /clusters  │  /validation  │     │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    SERVICES                              │   │
│  │  Clustering  │  GeoTagging  │  QR Generation  │  Auth   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Users     │  │   Reports    │  │ Validations  │          │
│  │   Collection │  │  Collection  │  │  Collection  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                       MongoDB                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.10+) |
| **Database** | MongoDB |
| **Authentication** | JWT (python-jose) + bcrypt |
| **Frontend** | Vanilla JS, CSS3 with modern animations |
| **Maps** | Leaflet.js with OpenStreetMap |
| **QR Generation** | qrcode + Pillow |
| **Image Processing** | Pillow (geo-annotation) |

### Dependencies
```
fastapi>=0.110
uvicorn[standard]>=0.27
SQLAlchemy>=2.0
pymongo>=4.6
pydantic>=2.6
email-validator>=2.1
bcrypt>=4.1
python-jose[cryptography]>=3.3
qrcode>=7.4
pillow>=10.2
python-dotenv>=1.0
```

---

## 👥 User Roles & Workflows

### Public User (Citizen)
```
Capture Photo → Check GPS Accuracy → Add Description → Submit Report → Track Status
                                                              │
                                                              ▼
                                                    Validate Nearby Reports
```

### Supervisor (Health Official / NGO)
```
View Reports → Accept/Reject → Assign Worker → Set Deadline → Verify Completion → Close
       │                              │
       ▼                              ▼
  View Clusters              Generate QR + Notify
```

### Field Worker
```
View Assignments → Scan QR → Navigate → Resolve Issue → Capture Completion Photo → Submit
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+
- MongoDB (local or Atlas)
- Node.js (optional, for frontend dev)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/shubhammgits/AquaAlert
   cd aquaalert
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .\.venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set:
   # JWT_SECRET=your-secure-random-string
   # MONGODB_URI=mongodb://localhost:27017
   # MONGODB_DB=aquaalert
   ```

5. **Start MongoDB** (if running locally)
   ```bash
   mongod
   ```

6. **Run the application**
   ```bash
   uvicorn --app-dir . backend.main:app --reload --host 127.0.0.1 --port 8000
   ```

---

## Render Deployment (Fix for Exit Status 3)

Use these exact settings in Render:

- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn --app-dir . backend.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`

Required environment variables:

- `JWT_SECRET` = your long random secret
- `MONGODB_URI` = your MongoDB Atlas connection string
- `MONGODB_DB` = `aquaalert`
- `SUPABASE_URL` = your Supabase project URL
- `SUPABASE_BUCKET` = your Supabase storage bucket name
- `SUPABASE_SERVICE_ROLE_KEY` = your Supabase service-role secret key

Notes:

- Do not use `--reload` on Render.
- App startup is now tolerant to temporary Mongo unavailability, so deploy should not fail during boot.
- Report photos, completion photos, and QR images are stored in Supabase Storage, while users/reports/status data stay in MongoDB.
- A Render blueprint file is included at `render.yaml`.

Recommended deployment flow:

1. Create the backend service on Render from this repo.
2. Add all required environment variables in the Render dashboard.
3. Make sure your Supabase bucket is created and public.
4. Deploy the backend and wait for the `/health` check to pass.
5. Open the deployed site and test login, report submit, assignment, completion, and QR display.

---

## Mobile App Path

The recommended mobile delivery is the Android wrapper in `android-app/`.

- It opens the deployed AquaAlert web app inside a native Android shell.
- It keeps the same backend, database, authentication, reports, and clustering logic.
- It still requires the FastAPI backend and MongoDB running behind it.

For the React frontend auth flow, use same-origin in production and set this only for local Vite development if needed:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login and get JWT |
| `GET` | `/auth/me` | Get current user info |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reports` | Create new report (with base64 image) |
| `GET` | `/reports` | List reports (filtered by role/district) |
| `GET` | `/reports/{id}` | Get report details |
| `POST` | `/reports/{id}/accept` | Accept report (supervisor) |
| `POST` | `/reports/{id}/assign` | Assign worker (supervisor) |
| `POST` | `/reports/{id}/complete` | Submit completion (worker) |
| `POST` | `/reports/{id}/verify` | Verify completion (supervisor) |

### Clusters
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/clusters` | Get all clusters with priority scores |
| `GET` | `/clusters?district=X` | Filter clusters by district |

### Validation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/validation/nearby` | Get nearby reports for validation |
| `POST` | `/validation/{id}/vote` | Vote on a report |

### Workers
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workers` | List available workers |
| `POST` | `/workers/location` | Update worker location |

---

## Database Schema

### Users Collection
```javascript
{
  id: Number,
  name: String,
  email: String,
  password_hash: String,
  role: "user" | "supervisor" | "worker",
  phone: String,
  district: String,
  state: String,
  city: String,
  is_available: Boolean,
  current_latitude: Number,
  current_longitude: Number,
  created_at: Date
}
```

### Reports Collection
```javascript
{
  id: Number,
  user_id: Number,
  latitude: Number,
  longitude: Number,
  location_accuracy: Number,
  image_path: String,
  description: String,
  contact_phone: String,
  district: String,
  state: String,
  city: String,
  severity: "Low" | "Medium" | "High",
  status: "submitted" | "accepted" | "assigned" | "completed" | "closed" | "rejected",
  cluster_id: String,
  qr_path: String,
  assigned_worker_id: Number,
  expected_completion_at: Date,
  completion_image_path: String,
  completed_at: Date,
  completion_verified_at: Date,
  created_at: Date
}
```

### Validations Collection
```javascript
{
  id: Number,
  report_id: Number,
  user_id: Number,
  vote: 1 | 0,
  created_at: Date
}
```

---

## 🔮 Future Scope

- [ ] **Push Notifications** — Real-time alerts for status changes
- [ ] **Offline Support** — PWA with local caching for low-connectivity areas
- [ ] **ML Integration** — Auto-severity prediction from images
- [ ] **Analytics Dashboard** — Historical trends and outbreak prediction
- [ ] **Multi-language Support** — Regional language interfaces
- [ ] **Integration APIs** — Connect with government health systems
- [ ] **Mobile Apps** — Native Android/iOS applications

---



