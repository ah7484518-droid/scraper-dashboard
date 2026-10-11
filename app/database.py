from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = "sqlite:///scraper.db"
engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    price: Mapped[float] = mapped_column(Float)
    rating: Mapped[int] = mapped_column(Integer)
    availability: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(500))
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


def init_db() -> None:
    """Create the tables if they do not exist yet."""
    Base.metadata.create_all(engine)


def save_books(books: list[dict]) -> int:
    """Replace the old data with the new results (so we never get duplicates)."""
    with Session(engine) as session:
        session.execute(delete(Book))
        session.add_all([Book(**book) for book in books])
        session.commit()
    return len(books)


def get_all_books() -> list[dict]:
    """Read all books from the database as a list of dictionaries."""
    with Session(engine) as session:
        rows = session.scalars(select(Book).order_by(Book.id)).all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "price": row.price,
                "rating": row.rating,
                "availability": row.availability,
                "url": row.url,
                "scraped_at": row.scraped_at.strftime("%Y-%m-%d %H:%M"),
            }
            for row in rows
        ]


if __name__ == "__main__":
    # Quick test: scrape 2 pages, save them, then read them back
    from app.scraper import scrape_books

    init_db()
    saved = save_books(scrape_books(max_pages=2))
    print(f"Saved {saved} books.")

    books = get_all_books()
    print(f"Books in database: {len(books)}")
    print("First book:", books[0])