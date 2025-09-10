# Gemini Instructions - Telemedicine Application

This file provides context and guidelines for Gemini when working on the telemedicine application codebase.

## Project Overview

**Application Type**: Telemedicine platform for patient-doctor consultations  
**Architecture**: Next.js frontend + FastAPI backend + PostgreSQL database  
**Deployment**: Docker containers for consistent environments  
**Key Features**: Medical records management, appointment booking, secure messaging, consultation notes

## Tech Stack & Framework Guidelines

### Backend (FastAPI + Python)

- **Language**: Python 3.11+ with type hints everywhere
- **Framework**: FastAPI with async/await patterns
- **Database**: PostgreSQL with SQLAlchemy 2.0+ async sessions
- **Authentication**: JWT tokens with role-based access control
- **Validation**: Pydantic models for request/response schemas
- **Testing**: pytest with real database integration tests

**Code Patterns**:

```python
# Always use type hints
async def get_user(user_id: UUID) -> User | None:
    async with get_async_session() as session:
        result = await session.get(User, user_id)
        return result

# Pydantic schemas for validation
class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

# FastAPI route with proper dependencies
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreateSchema,
    session: AsyncSession = Depends(get_async_session)
) -> UserResponse:
    # Implementation
```

### Frontend (Next.js + TypeScript)

- **Language**: TypeScript with strict mode enabled
- **Framework**: Next.js 14+ with App Router
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: Zustand for global state, React Query for server state
- **Forms**: React Hook Form with Zod validation
- **Testing**: Jest + React Testing Library

**Code Patterns**:

```typescript
// Always use TypeScript interfaces
interface PatientProfile {
  id: string;
  email: string;
  username: string;
  profileCompleted: boolean;
}

// React components with proper typing
interface PatientDashboardProps {
  patient: PatientProfile;
  onUpdateProfile: (data: ProfileUpdateData) => void;
}

export function PatientDashboard({
  patient,
  onUpdateProfile,
}: PatientDashboardProps) {
  // Implementation using shadcn/ui components
}

// API client with type safety
async function fetchPatientProfile(): Promise<PatientProfile> {
  const response = await fetch("/api/v1/auth/me");
  if (!response.ok) throw new Error("Failed to fetch profile");
  return response.json();
}
```

## Medical Domain Context

### Key Entities & Relationships

- **Patient**: Has medical records, books appointments, sends messages
- **Doctor**: Manages availability, views patient records, adds consultation notes
- **MedicalRecord**: Versioned patient data (medications, allergies, procedures)
- **Appointment**: Scheduled consultations with status tracking
- **Message**: Secure text communication between patients and doctors
- **ConsultationNote**: SOAP notes added by doctors after appointments

### Data Privacy & Security Requirements

- **HIPAA Compliance**: All medical data must be handled with appropriate security
- **Authentication**: JWT tokens with short expiry (15 min access, 7 day refresh)
- **Role-Based Access**: Patients access own data, doctors access assigned patients
- **Audit Trail**: Track all medical record changes with user attribution
- **Data Retention**: User-controlled with minimum 8 weeks requirement

### Medical Record Versioning

- **Immutable Versions**: Each update creates new version, preserves history
- **Chronological Access**: Doctors can view all versions in timeline
- **Change Attribution**: Track who made changes (patient vs doctor)
- **No Deletion**: Doctors cannot modify patient-entered data

## Authentication Patterns

### Patient Authentication

```python
# Patient registration with email + username
class PatientRegistration(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    first_name: str
    last_name: str
    date_of_birth: date
```

### Doctor Authentication

```python
# Doctor authentication with email + pre-assigned ID
class DoctorLogin(BaseModel):
    email: EmailStr
    doctor_id: str = Field(regex=r'^[A-Z0-9]+$')  # e.g., "DOC001"
    password: str
```

### JWT Implementation

```python
# JWT payload structure
{
    "sub": "user_uuid",
    "user_type": "patient" | "doctor",
    "exp": timestamp,
    "iat": timestamp
}
```

## Database Guidelines

### SQLAlchemy Models

```python
# Base model with common fields
class BaseModel:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

# Versioned medical records
class MedicalRecord(BaseModel):
    __tablename__ = "medical_records"

    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.user_id"))
    current_version: Mapped[int] = mapped_column(default=1)
    record_type: Mapped[str]  # 'medication', 'allergy', 'procedure', etc.

    # Relationship to versions
    versions: Mapped[List["MedicalRecordVersion"]] = relationship(back_populates="record")
```

### Migration Patterns

```python
# Always use Alembic for schema changes
# Migration example for adding new column
def upgrade():
    op.add_column('medical_records', sa.Column('retention_weeks', sa.Integer()))

def downgrade():
    op.drop_column('medical_records', 'retention_weeks')
```

## API Design Patterns

### REST Conventions

- `GET /patients/{id}/medical-records` - List patient's records
- `POST /medical-records` - Create new record (creates version 1)
- `PUT /medical-records/{id}` - Update record (creates new version)
- `GET /medical-records/{id}/versions` - Get all versions

### Error Handling

```python
# Consistent error responses
class ErrorResponse(BaseModel):
    error: str  # Error type identifier
    message: str  # Human-readable message
    details: Dict[str, Any] = {}  # Additional context

# HTTP status codes
# 200: Success
# 201: Created
# 400: Validation error
# 401: Authentication required
# 403: Access denied
# 404: Resource not found
# 422: Request validation failed
```

### WebSocket for Real-time

```python
# Real-time messaging endpoint
@app.websocket("/ws/messages/{user_id}")
async def websocket_messages(websocket: WebSocket, user_id: UUID):
    # Handle real-time message delivery
```

## Testing Requirements

### Backend Testing

```python
# Integration tests with real database
@pytest.mark.asyncio
async def test_medical_record_versioning(async_session, patient_user):
    # Create initial record
    record = await create_medical_record(patient_user.id, {...})
    assert record.current_version == 1

    # Update record (should create version 2)
    updated = await update_medical_record(record.id, {...})
    assert updated.current_version == 2

    # Verify both versions exist
    versions = await get_record_versions(record.id)
    assert len(versions) == 2
```

### Frontend Testing

```typescript
// Component testing with medical context
test("should display patient medical records", () => {
  const mockRecords = [
    { id: "1", type: "medication", title: "Lisinopril 10mg" },
    { id: "2", type: "allergy", title: "Penicillin allergy" },
  ];

  render(<MedicalRecords records={mockRecords} />);

  expect(screen.getByText("Lisinopril 10mg")).toBeInTheDocument();
  expect(screen.getByText("Penicillin allergy")).toBeInTheDocument();
});
```

## Component Library Usage

### shadcn/ui Components

```typescript
// Use shadcn/ui components for consistency
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";

// Medical questionnaire form example
<Form {...form}>
  <FormField
    control={form.control}
    name="allergies"
    render={({ field }) => (
      <FormItem>
        <FormLabel>Known Allergies</FormLabel>
        <FormControl>
          <Textarea placeholder="List any known allergies..." {...field} />
        </FormControl>
      </FormItem>
    )}
  />
</Form>;
```

### Tailwind CSS Patterns

```typescript
// Consistent styling patterns
const cardClasses = "bg-white border border-gray-200 rounded-lg shadow-sm p-6";
const buttonPrimary = "bg-blue-600 hover:bg-blue-700 text-white font-medium";
const textSecondary = "text-gray-600 text-sm";
```

## Common Patterns & Anti-Patterns

### ✅ Do This

- Use async/await for all database operations
- Validate all inputs with Pydantic/Zod schemas
- Include audit trails for medical data changes
- Use TypeScript interfaces for all data structures
- Follow REST conventions for API endpoints
- Use shadcn/ui components for UI consistency

### ❌ Avoid This

- Synchronous database calls in FastAPI
- Direct database access without session management
- Missing type annotations in Python/TypeScript
- Modifying medical records without versioning
- Hardcoded strings for user roles or statuses
- Custom CSS when shadcn/ui components exist

## Security Considerations

### Input Validation

```python
# Always validate medical data inputs
class MedicalRecordData(BaseModel):
    medication_name: str = Field(max_length=200)
    dosage: str = Field(max_length=100)
    frequency: str = Field(max_length=100)

    @validator('medication_name')
    def validate_medication_name(cls, v):
        # Add medical-specific validation
        return v.strip()
```

### Access Control

```python
# Check permissions for medical record access
async def check_medical_record_access(
    user: User,
    record: MedicalRecord
) -> bool:
    if user.user_type == "patient":
        return record.patient_id == user.id
    elif user.user_type == "doctor":
        # Doctor can access if they have appointment with patient
        return await has_appointment_with_patient(user.id, record.patient_id)
    return False
```

## Development Workflow

### File Organization

```
backend/
├── src/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── api/            # FastAPI routers
│   └── core/           # Config, database, security
└── tests/

frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/         # Next.js pages
│   ├── lib/           # Utilities, API clients
│   ├── hooks/         # Custom React hooks
│   └── types/         # TypeScript definitions
└── tests/
```

### Git Commit Patterns

- `feat: add medical record versioning API`
- `fix: resolve appointment booking validation`
- `test: add integration tests for messaging`
- `docs: update API documentation`

## Recent Changes & Context

- **Feature Branch**: `001-build-a-telemedicine`
- **Current Phase**: Initial implementation planning
- **Key Decisions**:
  - Modular monolith architecture for simplicity
  - JWT authentication with dual flows (patient/doctor)
  - Versioned medical records with audit trail
  - Docker-first development environment

---

When working on this codebase, prioritize:

1. **Data Security**: All medical data handling must be secure and auditable
2. **Type Safety**: Use TypeScript/Python type hints throughout
3. **Testing**: Write tests before implementation (TDD approach)
4. **Accessibility**: UI components must be accessible for healthcare use
5. **Performance**: API responses <200ms, page loads <2s
6. **Documentation**: Keep API docs and code comments current
