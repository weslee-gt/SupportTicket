from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, init_db
import crud
import schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    init_db()
    yield


app = FastAPI(
    title="Support Ticket Portal API",
    description="REST API for managing internal support tickets with status and priority tracking.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration to allow local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def read_root():
    return {"message": "Support Ticket Portal API is running", "docs": "/docs"}


@app.get("/api/health", tags=["General"])
def health_check():
    return {"status": "healthy"}


@app.get(
    "/api/tickets",
    response_model=List[schemas.TicketResponse],
    summary="List all tickets",
    tags=["Tickets"],
)
def list_tickets(
    status: Optional[schemas.StatusEnum] = Query(
        default=None, description="Filter tickets by status"
    ),
    priority: Optional[schemas.PriorityEnum] = Query(
        default=None, description="Filter tickets by priority"
    ),
    q: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Case-insensitive search across title, description and requester name",
    ),
    db: Session = Depends(get_db),
):
    """Retrieve all support tickets, optionally filtered by status, priority and/or a text search."""
    status_filter = status.value if status else None
    priority_filter = priority.value if priority else None
    return crud.get_tickets(db, status=status_filter, priority=priority_filter, q=q)


@app.post(
    "/api/tickets",
    response_model=schemas.TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a ticket",
    tags=["Tickets"],
)
def create_ticket(
    ticket_in: schemas.TicketCreate,
    db: Session = Depends(get_db),
):
    """Create a new support ticket."""
    return crud.create_ticket(db, ticket_in=ticket_in)


@app.get(
    "/api/tickets/{ticket_id}",
    response_model=schemas.TicketResponse,
    summary="Get a ticket by ID",
    tags=["Tickets"],
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single support ticket by its ID."""
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} not found",
        )
    return db_ticket


@app.patch(
    "/api/tickets/{ticket_id}",
    response_model=schemas.TicketResponse,
    summary="Update a ticket",
    tags=["Tickets"],
)
def update_ticket(
    ticket_id: int,
    ticket_update: schemas.TicketUpdate,
    db: Session = Depends(get_db),
):
    """Update fields of an existing support ticket."""
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} not found",
        )
    return crud.update_ticket(db, db_ticket=db_ticket, ticket_update=ticket_update)


@app.delete(
    "/api/tickets/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a ticket",
    tags=["Tickets"],
)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    """Delete a support ticket by its ID."""
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket with ID {ticket_id} not found",
        )
    crud.delete_ticket(db, db_ticket=db_ticket)
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
