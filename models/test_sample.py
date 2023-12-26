from database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List


# TODO: solve the malfunction of autoincrement
class TestSample(Base):
    __tablename__ = "test_sample"
    sid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    num: Mapped[int] = mapped_column(Integer, autoincrement=True)
    input: Mapped[str] = mapped_column(String)
    output: Mapped[str] = mapped_column(String)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.pid"))
    problem: Mapped["Problem"] = relationship(back_populates="samples")
