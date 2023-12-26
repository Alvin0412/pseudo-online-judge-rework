from database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

class SourceCode(Base):
    __tablename__ = "source_code"
    code_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String, default="pseudocode")
    code: Mapped[str] = mapped_column(String, nullable=False)
    pid: Mapped[int] = mapped_column(ForeignKey("problem.pid"))
    problem: Mapped["Problem"] = relationship()
    sid: Mapped[str] = mapped_column(String,nullable=False)