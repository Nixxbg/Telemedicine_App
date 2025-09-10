# Quickstart Guide - Telemedicine Application

**Feature**: Telemedicine Application  
**Branch**: `001-build-a-telemedicine`  
**Date**: September 10, 2025

## Overview

This quickstart guide provides step-by-step instructions to set up, run, and test the telemedicine application locally. The application consists of a Next.js frontend, FastAPI backend, and PostgreSQL database, all containerized with Docker.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Modern web browser

## Quick Setup (Docker)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd Telemedicine_App

# Create environment file from template
cp .env.example .env

# Edit .env with your local settings
# Default values should work for local development
```

### 2. Start the Application

```bash
# Start all services (database, backend, frontend)
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

### 3. Verify Services

```bash
# Check all services are running
docker-compose ps

# Expected services:
# - telemedicine_db (PostgreSQL)
# - telemedicine_backend (FastAPI)
# - telemedicine_frontend (Next.js)
```

## Service URLs

Once running, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)

## Initial Data Setup

### 1. Database Migration

```bash
# Run database migrations
docker-compose exec backend alembic upgrade head

# Verify migration status
docker-compose exec backend alembic current
```

### 2. Create Initial Doctor Records

```bash
# Create sample doctor accounts (hardcoded doctor IDs)
docker-compose exec backend python -m scripts.create_sample_doctors

# Expected output:
# ✅ Created doctor: DOC001 - Dr. Sarah Smith (Internal Medicine, Cardiology)
# ✅ Created doctor: DOC002 - Dr. Michael Johnson (Family Medicine)
# ✅ Created doctor: DOC003 - Dr. Emily Davis (Pediatrics, Immunology)
```

## User Journey Testing

### 1. Patient Registration and Profile Setup

#### Step 1: Register New Patient

```bash
# Test patient registration via API
curl -X POST http://localhost:8000/api/v1/auth/register/patient \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "username": "johndoe123",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "phone_number": "+1234567890"
  }'
```

**Expected Response**: 201 Created with JWT tokens

#### Step 2: Complete Medical Questionnaire

```bash
# Login and get access token
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john.doe@example.com", "password": "SecurePass123!"}' | \
  jq -r '.access_token')

# Start questionnaire (family history section)
curl -X PUT http://localhost:8000/api/v1/questionnaire \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "family_history_completed": true,
    "family_history_data": {
      "diabetes": "Father diagnosed at age 55",
      "heart_disease": "Mother has hypertension",
      "cancer": "No family history"
    }
  }'
```

**Expected Response**: 200 OK with updated questionnaire progress

#### Step 3: Add Medical Records

```bash
# Add medication record
curl -X POST http://localhost:8000/api/v1/medical-records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "record_type": "medication",
    "title": "Daily Blood Pressure Medication",
    "data": {
      "medication_name": "Lisinopril",
      "dosage": "10mg",
      "frequency": "Once daily",
      "start_date": "2025-01-01",
      "prescribing_doctor": "Dr. Smith"
    }
  }'
```

**Expected Response**: 201 Created with medical record details

### 2. Doctor Authentication and Setup

#### Step 1: Doctor Login

```bash
# Login with pre-assigned doctor ID
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dr.smith@example.com",
    "password": "DoctorPass123!"
  }'
```

**Expected Response**: 200 OK with JWT tokens and doctor profile

#### Step 2: Set Availability

```bash
# Get doctor access token
DOCTOR_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "dr.smith@example.com", "password": "DoctorPass123!"}' | \
  jq -r '.access_token')

# Set weekday availability
curl -X PUT http://localhost:8000/api/v1/doctors/availability \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "time_zone": "America/New_York",
    "availability": [
      {
        "day_of_week": 1,
        "start_time": "09:00",
        "end_time": "17:00",
        "appointment_duration_minutes": 30,
        "buffer_minutes": 15
      },
      {
        "day_of_week": 2,
        "start_time": "09:00",
        "end_time": "17:00",
        "appointment_duration_minutes": 30,
        "buffer_minutes": 15
      }
    ]
  }'
```

**Expected Response**: 200 OK with availability settings

### 3. Appointment Booking Flow

#### Step 1: Find Available Doctors

```bash
# Patient searches for doctors
curl -X GET "http://localhost:8000/api/v1/doctors?specialization=Internal%20Medicine" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expected Response**: 200 OK with list of available doctors

#### Step 2: Check Doctor Availability

```bash
# Get doctor availability for next week
DOCTOR_ID="123e4567-e89b-12d3-a456-426614174001"
curl -X GET "http://localhost:8000/api/v1/doctors/$DOCTOR_ID/availability?from_date=$(date -d '+1 week' '+%Y-%m-%d')&to_date=$(date -d '+2 weeks' '+%Y-%m-%d')" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expected Response**: 200 OK with available time slots

#### Step 3: Book Appointment

```bash
# Book appointment with available doctor
curl -X POST http://localhost:8000/api/v1/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "doctor_id": "'$DOCTOR_ID'",
    "scheduled_start": "2025-09-15T14:00:00Z",
    "scheduled_end": "2025-09-15T14:30:00Z",
    "appointment_type": "consultation",
    "reason_for_visit": "Regular check-up and blood pressure monitoring"
  }'
```

**Expected Response**: 201 Created with appointment details

### 4. Messaging System Testing

#### Step 1: Patient Sends Message

```bash
# Get appointment ID from booking response
APPOINTMENT_ID="456e7890-e12c-34d5-b678-526614174002"

# Patient sends message to doctor
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "recipient_id": "'$DOCTOR_ID'",
    "appointment_id": "'$APPOINTMENT_ID'",
    "content": "Hello Dr. Smith, I have a question about my medication dosage."
  }'
```

**Expected Response**: 201 Created with message details

#### Step 2: Doctor Responds

```bash
# Doctor replies to patient message
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "recipient_id": "123e4567-e89b-12d3-a456-426614174000",
    "appointment_id": "'$APPOINTMENT_ID'",
    "content": "Hello John, I would be happy to discuss your medication. What specific concerns do you have?"
  }'
```

**Expected Response**: 201 Created with message details

### 5. Consultation Notes

#### Step 1: Complete Appointment

```bash
# Doctor marks appointment as completed
curl -X PUT http://localhost:8000/api/v1/appointments/$APPOINTMENT_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "status": "completed"
  }'
```

**Expected Response**: 200 OK with updated appointment

#### Step 2: Add Consultation Notes

```bash
# Doctor adds SOAP notes after consultation
curl -X POST http://localhost:8000/api/v1/consultation-notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DOCTOR_TOKEN" \
  -d '{
    "appointment_id": "'$APPOINTMENT_ID'",
    "subjective": "Patient reports feeling well since starting medication. No side effects noted.",
    "objective": "Blood pressure: 120/80 mmHg. Heart rate: 72 bpm. Patient appears well.",
    "assessment": "Hypertension well controlled on current medication regimen.",
    "plan": "Continue current medication. Follow up in 4 weeks. Patient to monitor BP at home.",
    "follow_up_required": true,
    "follow_up_timeframe": "4 weeks",
    "medications_prescribed": [
      {
        "name": "Lisinopril",
        "dosage": "10mg",
        "frequency": "Once daily",
        "duration": "30 days"
      }
    ]
  }'
```

**Expected Response**: 201 Created with consultation note

## Frontend Testing (Browser)

### 1. Access the Application

1. Open browser to http://localhost:3000
2. Verify landing page loads correctly
3. Check responsive design on different screen sizes

### 2. Patient Registration Flow

1. Click "Register as Patient"
2. Fill out registration form
3. Verify email validation
4. Complete registration and automatic login
5. Navigate to medical questionnaire
6. Fill out sections partially (test progress saving)
7. Complete questionnaire sections
8. Add medical records through UI

### 3. Doctor Login Flow

1. Use doctor credentials: `dr.smith@example.com` / `DoctorPass123!`
2. Access doctor dashboard
3. Set availability through calendar interface
4. View upcoming appointments
5. Access patient medical records (for scheduled appointments)

### 4. Appointment Booking (Patient)

1. Browse available doctors
2. Filter by specialization
3. Select doctor and view profile
4. Choose available time slot
5. Complete booking form
6. Receive booking confirmation

### 5. Messaging Interface

1. Navigate to messages from appointment
2. Send message to doctor
3. Receive real-time message notifications
4. Test message read receipts
5. Test conversation history

## Data Verification

### 1. Database Inspection

```bash
# Connect to database
docker-compose exec db psql -U telemedicine -d telemedicine_db

# Check patient registration
SELECT id, email, username, user_type FROM users WHERE user_type = 'patient';

# Check medical records with versions
SELECT mr.title, mr.current_version, mrv.version_number, mrv.created_at
FROM medical_records mr
JOIN medical_record_versions mrv ON mr.id = mrv.medical_record_id
ORDER BY mr.updated_at DESC;

# Check appointments
SELECT a.id, p.username as patient, d.doctor_id, a.status, a.scheduled_start
FROM appointments a
JOIN patients p ON a.patient_id = p.user_id
JOIN doctors d ON a.doctor_id = d.user_id
ORDER BY a.scheduled_start;
```

### 2. API Response Validation

```bash
# Test API schema compliance
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'

# Verify JWT token structure
echo $ACCESS_TOKEN | cut -d'.' -f2 | base64 -d | jq '.'
```

## Performance Testing

### 1. Load Testing (Optional)

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API performance
ab -n 100 -c 10 -H "Authorization: Bearer $ACCESS_TOKEN" \
  http://localhost:8000/api/v1/medical-records

# Expected: <200ms average response time
```

### 2. Frontend Performance

1. Open browser DevTools
2. Navigate to Lighthouse tab
3. Run performance audit
4. Expected scores: >90 for Performance, Accessibility, Best Practices

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check port conflicts
netstat -tulpn | grep -E ':(3000|8000|5432)'

# Reset Docker environment
docker-compose down -v
docker-compose up -d
```

#### Database Connection Issues

```bash
# Check database logs
docker-compose logs db

# Recreate database volume
docker-compose down -v
docker volume rm telemedicine_app_postgres_data
docker-compose up -d
```

#### Frontend Build Issues

```bash
# Rebuild frontend container
docker-compose build frontend
docker-compose up -d frontend
```

#### API Authentication Issues

```bash
# Verify JWT token expiry
echo $ACCESS_TOKEN | cut -d'.' -f2 | base64 -d | jq '.exp'

# Get fresh token
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john.doe@example.com", "password": "SecurePass123!"}' | \
  jq -r '.access_token')
```

## Cleanup

### Stop Services

```bash
# Stop all services
docker-compose down

# Remove volumes (data will be lost)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Next Steps

After completing this quickstart:

1. **Development Setup**: Set up local development environment without Docker
2. **Testing**: Run comprehensive test suites
3. **Deployment**: Deploy to staging/production environment
4. **Monitoring**: Set up logging and monitoring systems

## Success Criteria

✅ **All services start successfully**  
✅ **Patient can register and complete medical questionnaire**  
✅ **Doctor can set availability and manage appointments**  
✅ **Appointment booking flow works end-to-end**  
✅ **Messaging system enables patient-doctor communication**  
✅ **Medical records are versioned and accessible**  
✅ **Consultation notes can be added and viewed**  
✅ **API responses match OpenAPI specifications**  
✅ **Frontend is responsive and accessible**  
✅ **Database maintains data integrity**

---

**Quickstart Status**: ✅ COMPLETE - Ready for development and testing
