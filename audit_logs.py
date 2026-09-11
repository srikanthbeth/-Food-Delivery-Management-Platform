from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from utils.enums import UserRole

from services.audit_log_service import get_audit_logs_service
from schemas.audit_log import AuditLogResponse


router = APIRouter(
    prefix="/audit-logs",
    tags=["Security & Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    user_id: int | None = Query(
        default=None,
        description="Filter audit logs by user ID",
    ),
    action: str | None = Query(
        default=None,
        description="Filter audit logs by action",
    ),
    resource_type: str | None = Query(
        default=None,
        description="Filter audit logs by resource type",
    ),
    resource_id: int | None = Query(
        default=None,
        description="Filter audit logs by resource ID",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise PermissionError(
            "Only administrators can view audit logs"
        )

    return get_audit_logs_service(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
    )