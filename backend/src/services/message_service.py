"""
Message service for secure communication and real-time messaging

This service handles:
- Secure text messaging between patients and doctors
- Message threading and conversation management
- Real-time message delivery and notifications
- Message read status tracking
- System notifications and automated messages
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.appointment import Appointment
from src.models.message import Message, MessageType
from src.models.user import User, UserType


class MessageService:
    """Service for message management and real-time communication"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def send_message(
        self,
        sender_id: UUID,
        recipient_id: UUID,
        content: str,
        sender_user_type: UserType,
        message_type: MessageType = MessageType.TEXT,
        appointment_id: Optional[UUID] = None,
    ) -> Message:
        """
        Send a message between users

        Args:
            sender_id: ID of the user sending the message
            recipient_id: ID of the user receiving the message
            content: Message content
            sender_user_type: Type of user sending the message
            message_type: Type of message (text or system notification)
            appointment_id: Optional appointment context

        Returns:
            Created Message object

        Raises:
            HTTPException: If validation fails or access denied
        """
        # Validate message content
        if not content or len(content.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty",
            )

        if len(content) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot exceed 2000 characters",
            )

        # Validate sender and recipient exist
        await self._validate_users_exist(sender_id, recipient_id)

        # Validate messaging permissions
        await self._check_messaging_permissions(
            sender_id, recipient_id, sender_user_type, appointment_id
        )

        # Create message
        message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content.strip(),
            message_type=message_type,
            appointment_id=appointment_id,
        )

        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_message(
        self, message_id: UUID, requesting_user_id: UUID
    ) -> Optional[Message]:
        """
        Get a message by ID with access control

        Args:
            message_id: Message ID
            requesting_user_id: User requesting the message

        Returns:
            Message object or None if not found/no access
        """
        stmt = (
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.recipient),
                selectinload(Message.appointment),
            )
            .where(Message.id == message_id)
        )
        result = await self.session.execute(stmt)
        message = result.scalar_one_or_none()

        if not message:
            return None

        # Check if user has access to this message
        if not message.can_be_read_by(requesting_user_id):
            return None

        return message

    async def get_conversation(
        self,
        user1_id: UUID,
        user2_id: UUID,
        requesting_user_id: UUID,
        appointment_id: Optional[UUID] = None,
        limit: Optional[int] = 50,
        offset: int = 0,
    ) -> List[Message]:
        """
        Get conversation between two users

        Args:
            user1_id: First user ID
            user2_id: Second user ID
            requesting_user_id: User requesting the conversation
            appointment_id: Optional filter by appointment
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of Message objects (newest first)

        Raises:
            HTTPException: If access denied
        """
        # Check if requesting user is part of the conversation
        if requesting_user_id not in [user1_id, user2_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation",
            )

        # Build query conditions
        conditions = [
            or_(
                and_(Message.sender_id == user1_id, Message.recipient_id == user2_id),
                and_(Message.sender_id == user2_id, Message.recipient_id == user1_id),
            )
        ]

        if appointment_id:
            conditions.append(Message.appointment_id == appointment_id)

        stmt = (
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.recipient),
            )
            .where(and_(*conditions))
            .order_by(desc(Message.sent_at))
            .offset(offset)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_conversations(
        self, user_id: UUID, limit: Optional[int] = 20
    ) -> List[Dict[str, Any]]:
        """
        Get list of conversations for a user

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries with latest message info
        """
        # Get all messages where user is sender or recipient
        stmt = (
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.recipient),
                selectinload(Message.appointment),
            )
            .where(or_(Message.sender_id == user_id, Message.recipient_id == user_id))
            .order_by(desc(Message.sent_at))
        )

        result = await self.session.execute(stmt)
        all_messages = list(result.scalars().all())

        # Group messages by conversation partner
        conversations = {}
        for message in all_messages:
            partner_id = (
                message.recipient_id
                if message.sender_id == user_id
                else message.sender_id
            )

            if partner_id not in conversations:
                partner = (
                    message.recipient
                    if message.sender_id == user_id
                    else message.sender
                )
                conversations[partner_id] = {
                    "partner_id": str(partner_id),
                    "partner_email": partner.email,
                    "partner_type": partner.user_type.value,
                    "latest_message": {
                        "id": str(message.id),
                        "content": message.content_preview,
                        "sent_at": message.sent_at.isoformat(),
                        "is_read": message.is_read,
                        "sender_id": str(message.sender_id),
                        "message_type": message.message_type.value,
                    },
                    "unread_count": 0,
                    "total_messages": 0,
                    "appointment_id": (
                        str(message.appointment_id) if message.appointment_id else None
                    ),
                }

            # Count messages and unread messages
            conversations[partner_id]["total_messages"] += 1
            if not message.is_read and message.recipient_id == user_id:
                conversations[partner_id]["unread_count"] += 1

        # Convert to list and sort by latest message timestamp
        conversation_list = list(conversations.values())
        conversation_list.sort(
            key=lambda x: x["latest_message"]["sent_at"], reverse=True
        )

        return conversation_list[:limit] if limit else conversation_list

    async def mark_message_as_read(
        self, message_id: UUID, user_id: UUID
    ) -> Optional[Message]:
        """
        Mark a message as read

        Args:
            message_id: Message ID
            user_id: User marking the message as read

        Returns:
            Updated Message object or None if not found/no access
        """
        message = await self.get_message(message_id, user_id)
        if not message:
            return None

        # Only the recipient can mark a message as read
        if message.recipient_id != user_id:
            return None

        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(message)

        return message

    async def mark_conversation_as_read(
        self, sender_id: UUID, recipient_id: UUID
    ) -> int:
        """
        Mark all messages in a conversation as read

        Args:
            sender_id: Sender user ID
            recipient_id: Recipient user ID (user marking messages as read)

        Returns:
            Number of messages marked as read
        """
        # Get unread messages from sender to recipient
        stmt = select(Message).where(
            and_(
                Message.sender_id == sender_id,
                Message.recipient_id == recipient_id,
                Message.is_read.is_(False),
            )
        )

        result = await self.session.execute(stmt)
        unread_messages = list(result.scalars().all())

        # Mark all as read
        count = 0
        current_time = datetime.now(timezone.utc)
        for message in unread_messages:
            message.is_read = True
            message.read_at = current_time
            count += 1

        if count > 0:
            await self.session.commit()

        return count

    async def get_unread_message_count(self, user_id: UUID) -> int:
        """
        Get count of unread messages for a user

        Args:
            user_id: User ID

        Returns:
            Number of unread messages
        """
        stmt = select(Message).where(
            and_(Message.recipient_id == user_id, Message.is_read.is_(False))
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        return len(messages)

    async def search_messages(
        self,
        user_id: UUID,
        query: str,
        conversation_partner_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[Message]:
        """
        Search messages for a user

        Args:
            user_id: User performing the search
            query: Search query
            conversation_partner_id: Optional filter by conversation partner
            limit: Maximum results to return

        Returns:
            List of matching Message objects
        """
        if len(query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters",
            )

        # Base conditions: user is sender or recipient
        conditions = [
            or_(Message.sender_id == user_id, Message.recipient_id == user_id),
            Message.content.ilike(f"%{query}%"),  # Case-insensitive search
        ]

        # Optional filter by conversation partner
        if conversation_partner_id:
            conditions.append(
                or_(
                    and_(
                        Message.sender_id == user_id,
                        Message.recipient_id == conversation_partner_id,
                    ),
                    and_(
                        Message.sender_id == conversation_partner_id,
                        Message.recipient_id == user_id,
                    ),
                )
            )

        stmt = (
            select(Message)
            .options(
                selectinload(Message.sender),
                selectinload(Message.recipient),
            )
            .where(and_(*conditions))
            .order_by(desc(Message.sent_at))
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def send_system_notification(
        self,
        recipient_id: UUID,
        content: str,
        appointment_id: Optional[UUID] = None,
    ) -> Message:
        """
        Send a system notification message

        Args:
            recipient_id: User to receive the notification
            content: Notification content
            appointment_id: Optional appointment context

        Returns:
            Created Message object
        """
        # Use a system user ID (you might want to create a dedicated system user)
        # For now, we'll use the recipient as sender for system messages
        message = Message(
            sender_id=recipient_id,  # System messages sender = recipient
            recipient_id=recipient_id,
            content=content,
            message_type=MessageType.SYSTEM_NOTIFICATION,
            appointment_id=appointment_id,
        )

        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def delete_message(self, message_id: UUID, requesting_user_id: UUID) -> bool:
        """
        Delete a message (soft delete - mark as deleted)

        Args:
            message_id: Message ID
            requesting_user_id: User requesting deletion

        Returns:
            True if deleted, False if not found/no access
        """
        message = await self.get_message(message_id, requesting_user_id)
        if not message:
            return False

        # Only sender can delete their own messages
        if message.sender_id != requesting_user_id:
            return False

        # For v1, we'll do hard delete. In production, consider soft delete
        await self.session.delete(message)
        await self.session.commit()
        return True

    async def _validate_users_exist(self, sender_id: UUID, recipient_id: UUID) -> None:
        """Validate that both sender and recipient users exist"""
        stmt = select(User).where(User.id.in_([sender_id, recipient_id]))
        result = await self.session.execute(stmt)
        users = list(result.scalars().all())

        if len(users) != 2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found",
            )

    async def _check_messaging_permissions(
        self,
        sender_id: UUID,
        recipient_id: UUID,
        sender_user_type: UserType,
        appointment_id: Optional[UUID] = None,
    ) -> None:
        """
        Check if users are allowed to message each other

        For v1: Allow messaging between:
        - Patient and Doctor (if they have an appointment together)
        - System notifications (always allowed)
        """
        if sender_id == recipient_id:
            # Allow system notifications to self
            return

        # Get user types
        stmt = select(User).where(User.id.in_([sender_id, recipient_id]))
        result = await self.session.execute(stmt)
        users = {user.id: user for user in result.scalars().all()}

        sender_user = users.get(sender_id)
        recipient_user = users.get(recipient_id)

        if not sender_user or not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found",
            )

        # Check if one is patient and other is doctor
        user_types = {sender_user.user_type, recipient_user.user_type}
        if user_types != {UserType.PATIENT, UserType.DOCTOR}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Messaging is only allowed between patients and doctors",
            )

        # For v1, we'll allow all patient-doctor messaging
        # In production, you'd check for active appointments or
        # doctor-patient relationships

        # Optional: If appointment_id is provided, verify both users are part of it
        if appointment_id:
            stmt = select(Appointment).where(Appointment.id == appointment_id)
            result = await self.session.execute(stmt)
            appointment = result.scalar_one_or_none()

            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found",
                )

            if not (
                {appointment.patient_id, appointment.doctor_id}
                == {sender_id, recipient_id}
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Users are not part of the specified appointment",
                )
