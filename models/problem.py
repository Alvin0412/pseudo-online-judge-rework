from database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

class Problem(Base):
    __tablename__ = "problem"
    pid: Mapped[int] = mapped_column(Integer, unique=True, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    input: Mapped[str] = mapped_column(String)
    output: Mapped[str] = mapped_column(String)
    sample_input: Mapped[str] = mapped_column(String)
    sample_output: Mapped[str] = mapped_column(String)
    labels: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    hint: Mapped[str] = mapped_column(String)
    difficulty: Mapped[str] = mapped_column(String, default="easy")
    time_limit: Mapped[str] = mapped_column(String, default="1")
    memory_limit: Mapped[str] = mapped_column(String, default="16")
    accepted: Mapped[int] = mapped_column(Integer, default=0)
    submit: Mapped[int] = mapped_column(Integer, default=0)
    solved: Mapped[int] = mapped_column(Integer, default=0)
    defunct: Mapped[bool] = mapped_column(Boolean, default=False)
    samples: Mapped[List["TestSample"]] = relationship(back_populates='problem')
