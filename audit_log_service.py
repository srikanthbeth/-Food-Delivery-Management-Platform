from sqlalchemy.orm import Session

from repositories.audit_log_repository import (
    create_audit_log,
    get_audit_log_by_id,
    get_audit_logs,
    get_audit_logs_by_resource,
    get_audit_logs_by_user,
)
from utils.exceptions import ResourceNotFoundException


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    description: str | None = None,
    ip_address: str | None = None,
):
    return create_audit_log(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
    )


def get_audit_log_service(
    db: Session,
    audit_log_id: int,
):
    audit_log = get_audit_log_by_id(
        db=db,
        audit_log_id=audit_log_id,
    )

    if not audit_log:
        raise ResourceNotFoundException(
            "Audit log not found"
        )

    return audit_log


def get_audit_logs_service(
    db: Session,
    user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
):
    return get_audit_logs(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
    )


def get_user_audit_logs_service(
    db: Session,
    user_id: int,
):
    return get_audit_logs_by_user(
        db=db,
        user_id=user_id,
    )


def get_resource_audit_logs_service(
    db: Session,
    resource_type: str,
    resource_id: int,
):
    return get_audit_logs_by_resource(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
    )