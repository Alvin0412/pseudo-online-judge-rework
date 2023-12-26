from database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

class Submission(Base):
    __tablename__ = "submission"
    submit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_id: Mapped[str] = mapped_column(ForeignKey("source_code.code_id"))
    source_code: Mapped["SourceCode"] = relationship()
    runtime_infos: Mapped[List["RuntimeInfo"]] = relationship(back_populates='submission')
    sid: Mapped[str] = mapped_column(String,nullable=False)
    pid: Mapped[int] = mapped_column(ForeignKey("problem.pid"))
    valid: Mapped[bool] = mapped_column(Boolean,nullable=True)

