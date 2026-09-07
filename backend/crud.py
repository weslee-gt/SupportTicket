from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
import models
import schemas

UTC8 = timezone(timedelta(hours=8))

def get_tickets(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[models.Ticket]:
    """Retrieve one page of tickets, optionally filtered by status and/or priority."""
    query = db.query(models.Ticket)
    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    return (
        query.order_by(models.Ticket.createdAt.desc(), models.Ticket.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    """Retrieve a single ticket by its ID."""
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()


def create_ticket(db: Session, ticket_in: schemas.TicketCreate) -> models.Ticket:
    """Create a new support ticket in the database."""
    db_ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        priority=ticket_in.priority.value,
        status=ticket_in.status.value if ticket_in.status else "Open",
        requesterName=ticket_in.requesterName,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(
    db: Session, db_ticket: models.Ticket, ticket_update: schemas.TicketUpdate
) -> models.Ticket:
    """Update fields of an existing ticket."""
    update_data = ticket_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            # If value is an Enum, extract its string value
            if hasattr(value, "value"):
                value = value.value
            setattr(db_ticket, field, value)

    db_ticket.updatedAt = datetime.now(UTC8)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, db_ticket: models.Ticket) -> None:
    """Delete a ticket from the database."""
    db.delete(db_ticket)
    db.commit()
