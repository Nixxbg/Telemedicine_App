"""
Authentication service for user registration, login, and JWT token management

This service handles:
- User registration for patients and doctors
- Password verification and authentication
- JWT token creation and validation
- User session management
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

import bcrypt
from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.models.doctor import Doctor
from src.models.patient import Patient
from src.models.user import User, UserType


class AuthService:
    """Authentication service for user management and JWT operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def create_access_token(user_id: UUID, user_type: UserType) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "user_type": user_type.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: UUID, user_type: UserType) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sub": str(user_id),
            "user_type": user_type.value,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }
        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                )

            return payload

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID with related data"""
        stmt = (
            select(User)
            .options(selectinload(User.patient), selectinload(User.doctor))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_patient(
        self,
        email: str,
        password: str,
        username: str,
        first_name: str,
        last_name: str,
        date_of_birth: str,  # Will be converted to date
        phone_number: Optional[str] = None,
        emergency_contact_name: Optional[str] = None,
        emergency_contact_phone: Optional[str] = None,
    ) -> tuple[User, Patient]:
        """
        Register a new patient user.

        Args:
            email: Unique patient email address.
            password: Plain text password to hash and store.
            username: Unique patient username.
            first_name: Patient first name.
            last_name: Patient last name.
            date_of_birth: Date of birth string in ISO format (YYYY-MM-DD).
            phone_number: Optional patient phone number in E.164 format.
            emergency_contact_name: Optional emergency contact name.
            emergency_contact_phone: Optional emergency contact phone number.

        Returns:
            tuple[User, Patient]: Newly created user and patient records.

        Raises:
            HTTPException: If email or username already exists.
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if username already exists
        stmt = select(Patient).where(Patient.username == username)
        result = await self.session.execute(stmt)
        existing_patient = result.scalar_one_or_none()
        if existing_patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

        # Create user
        user = User(
            id=uuid4(),
            email=email,
            password_hash=self.hash_password(password),
            user_type=UserType.PATIENT,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()  # Get the user ID

        # Parse date of birth
        from datetime import datetime

        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

        # Create patient profile
        patient = Patient(
            user_id=user.id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=dob,
            phone_number=phone_number,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
            profile_completed=False,
        )
        self.session.add(patient)

        await self.session.commit()
        await self.session.refresh(user)
        await self.session.refresh(patient)

        return user, patient

    async def register_doctor(
        self,
        email: str,
        password: str,
        doctor_id: str,
        first_name: str,
        last_name: str,
        specializations: list[str],
        license_number: Optional[str] = None,
        bio: Optional[str] = None,
        years_experience: Optional[int] = None,
        is_accepting_patients: bool = False,
    ) -> tuple[User, Doctor]:
        """
        Register a new doctor user.

        Args:
            email: Unique doctor email address.
            password: Plain text password to hash and store.
            doctor_id: Pre-assigned doctor identifier.
            first_name: Doctor first name.
            last_name: Doctor last name.
            specializations: List of doctor specializations.
            license_number: Optional medical license number.
            bio: Optional professional biography.
            years_experience: Optional years of experience value.
            is_accepting_patients: Whether doctor currently accepts patients.

        Returns:
            tuple[User, Doctor]: Newly created user and doctor records.

        Raises:
            HTTPException: If email or doctor_id already exists.
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if doctor_id already exists
        stmt = select(Doctor).where(Doctor.doctor_id == doctor_id)
        result = await self.session.execute(stmt)
        existing_doctor = result.scalar_one_or_none()
        if existing_doctor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor ID already exists",
            )

        if not specializations:
            raise HTTPException(  # pragma: no cover - validated upstream
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one specialization is required",
            )

        # Create user
        user = User(
            id=uuid4(),
            email=email,
            password_hash=self.hash_password(password),
            user_type=UserType.DOCTOR,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()  # Get the user ID

        # Create doctor profile
        doctor = Doctor(
            user_id=user.id,
            doctor_id=doctor_id,
            first_name=first_name,
            last_name=last_name,
            specializations=specializations,
            license_number=license_number,
            bio=bio,
            years_experience=years_experience,
            is_accepting_patients=is_accepting_patients,
        )
        self.session.add(doctor)

        await self.session.commit()
        await self.session.refresh(user)
        await self.session.refresh(doctor)

        return user, doctor

    async def authenticate_user(
        self, email: str, password: str, user_type: Optional[UserType] = None
    ) -> Optional[User]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: Plain text password
            user_type: Optional user type filter

        Returns:
            User object if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None

        # Check if user type matches if specified
        if user_type and user.user_type != user_type:
            return None

        # Check if user is active
        if not user.is_active:
            return None

        # Verify password
        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.session.commit()

        return user

    async def authenticate_doctor_with_id(
        self, email: str, doctor_id: str, password: str
    ) -> Optional[User]:
        """
        Authenticate doctor with email, doctor_id, and password

        Args:
            email: Doctor email
            doctor_id: Doctor ID (e.g., "DOC001")
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user or user.user_type != UserType.DOCTOR:
            return None

        # Check if user is active
        if not user.is_active:
            return None

        # Load doctor profile and verify doctor_id
        stmt = select(Doctor).where(Doctor.user_id == user.id)
        result = await self.session.execute(stmt)
        doctor = result.scalar_one_or_none()

        if not doctor or doctor.doctor_id != doctor_id:
            return None

        # Verify password
        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.session.commit()

        return user

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Generate new access and refresh tokens from a valid refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            tuple: (new_access_token, new_refresh_token)

        Raises:
            HTTPException: If refresh token is invalid or user not found
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        user_id = UUID(payload["sub"])
        user_type = UserType(payload["user_type"])

        # Verify user still exists and is active
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new tokens
        access_token = self.create_access_token(user_id, user_type)
        new_refresh_token = self.create_refresh_token(user_id, user_type)

        return access_token, new_refresh_token

    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token

        Args:
            token: JWT access token

        Returns:
            User object

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify access token
        payload = self.verify_token(token, "access")
        user_id = UUID(payload["sub"])

        # Get user
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        return user

    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate a user account

        Args:
            user_id: User ID to deactivate

        Returns:
            True if successful, False if user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        await self.session.commit()
        return True

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            True if successful, False if current password is invalid

        Raises:
            HTTPException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            return False

        # Update password
        user.password_hash = self.hash_password(new_password)
        await self.session.commit()
        return True
