# Telemedicine Application

A comprehensive telemedicine platform that enables patients to maintain digital medical records and book consultations with doctors through a secure web application.

## Features

- **Patient Management**: Digital medical records with version history
- **Doctor Portal**: Appointment management and patient consultation
- **Secure Messaging**: Real-time communication between patients and doctors
- **Appointment Booking**: Schedule consultations with available doctors
- **Medical Questionnaires**: Structured health assessments with progress saving
- **Role-based Authentication**: Separate flows for patients and doctors

## Tech Stack

### Backend

- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: Database ORM with async support
- **PostgreSQL**: Robust relational database
- **Pydantic**: Data validation and serialization
- **JWT**: Secure authentication tokens

### Frontend

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern UI components
- **Zustand**: Lightweight state management
- **React Query**: Server state management

### Infrastructure

- **Docker**: Containerized development environment
- **Docker Compose**: Multi-service orchestration

## Project Structure

```
telemedicine-app/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Configuration and utilities
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── services/       # Business logic services
│   └── tests/              # Backend tests
├── frontend/                # Next.js frontend
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Next.js pages
│   │   ├── lib/            # Utilities and API clients
│   │   ├── hooks/          # Custom React hooks
│   │   └── types/          # TypeScript type definitions
│   └── tests/              # Frontend tests
├── docker-compose.yml       # Docker services configuration
└── specs/                   # Project specifications and documentation
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start with Docker

1. Clone the repository
2. Start the development environment:

   ```bash
   docker-compose up --build
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Development Workflow

1. **Environment Setup**: Use Docker for consistent development
2. **Testing First**: Write contract tests before implementation (TDD)
3. **Database Migrations**: Use Alembic for schema changes
4. **Code Quality**: Follow linting and formatting standards
5. **Security**: Implement HIPAA-compliant data handling

## API Documentation

The backend provides comprehensive API documentation at `/docs` when running locally.

### Key Endpoints

- `POST /api/v1/auth/register` - Patient registration
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/medical-records` - List medical records
- `POST /api/v1/medical-records` - Create medical record
- `GET /api/v1/appointments` - List appointments
- `POST /api/v1/appointments` - Book appointment
- `GET /api/v1/messages` - List messages
- `WebSocket /ws/messages/{user_id}` - Real-time messaging

## Database Schema

The application uses PostgreSQL with the following core entities:

- **Users**: Base user information
- **Patients**: Patient-specific data
- **Doctors**: Doctor profiles and availability
- **MedicalRecords**: Versioned medical history
- **Appointments**: Scheduled consultations
- **Messages**: Communication between users
- **QuestionnaireProgress**: Health assessment progress

## Security

- JWT-based authentication with role-based access control
- Password hashing with secure algorithms
- Input validation and sanitization
- HIPAA-compliant data handling
- Audit trails for medical record changes

## Testing

The project follows a comprehensive testing strategy:

- **Contract Tests**: API endpoint validation
- **Integration Tests**: End-to-end workflow testing
- **Unit Tests**: Individual component testing

Run tests with:

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## Contributing

1. Follow the established coding standards
2. Write tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

This project is licensed under the MIT License.
