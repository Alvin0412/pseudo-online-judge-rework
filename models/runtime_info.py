from database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List


class RuntimeInfo(Base):
    __tablename__ = "runtime_info"
    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("test_sample.sid"))
    problem_id: Mapped[int] = mapped_column(ForeignKey("problem.pid"))
    status: Mapped[str] = mapped_column(String, nullable=False)
    msg: Mapped[str] = mapped_column(String, nullable=True)
    problem: Mapped["Problem"] = relationship()
    sample: Mapped["TestSample"] = relationship()
    submission_id: Mapped[int] = mapped_column(ForeignKey("submission.submit_id"))
    submission: Mapped["Submission"] = relationship(back_populates="runtime_infos")