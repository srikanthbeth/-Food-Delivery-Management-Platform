
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user

from schemas.notification import (
    NotificationResponse,
    NotificationReadResponse,
)

from services.notification_service import (
    get_notifications_service,
    get_unread_notifications_service,
    mark_notification_read_service,
)

from utils.exceptions import ResourceNotFoundException


router = APIRouter(
    tags=["Notifications"],
)


@router.get(
    "/notifications",
    response_model=list[NotificationResponse],
)
def get_notifications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_notifications_service(
            db,
            current_user,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.get(
    "/notifications/unread",
    response_model=list[NotificationResponse],
)
def get_unread_notifications(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_unread_notifications_service(
            db,
            current_user,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.put(
    "/notifications/{notification_id}/read",
    response_model=NotificationReadResponse,
)
def mark_notification_read(
    notification_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        notification = mark_notification_read_service(
            db,
            notification_id,
            current_user,
        )

        return {
            "success": True,
            "message": "Notification marked as read",
            "notification_id": notification.id,
            "is_read": notification.is_read,
        }

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
