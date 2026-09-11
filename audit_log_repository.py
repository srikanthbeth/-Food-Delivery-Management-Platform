from sqlalchemy.orm import Session

from models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    user_id: int | None,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    description: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
    )

    db.add(audit_log)

    # Do not commit here.
    # This allows the audit log to participate in the
    # same database transaction as the main operation.
    db.flush()

    return audit_log


def get_audit_log_by_id(
    db: Session,
    audit_log_id: int,
) -> AuditLog | None:
    return (
        db.query(AuditLog)
        .filter(AuditLog.id == audit_log_id)
        .first()
    )


def get_audit_logs(
    db: Session,
    user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
) -> list[AuditLog]:
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(
            AuditLog.user_id == user_id
        )

    if action is not None:
        query = query.filter(
            AuditLog.action == action
        )

    if resource_type is not None:
        query = query.filter(
            AuditLog.resource_type == resource_type
        )

    if resource_id is not None:
        query = query.filter(
            AuditLog.resource_id == resource_id
        )

    return (
        query
        .order_by(AuditLog.created_at.desc())
        .all()
    )


def get_audit_logs_by_user(
    db: Session,
    user_id: int,
) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )


def get_audit_logs_by_resource(
    db: Session,
    resource_type: str,
    resource_id: int,
) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        .order_by(AuditLog.created_at.desc())
        .all()
    )