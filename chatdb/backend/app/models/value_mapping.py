from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ValueMapping(Base):
    id = Column(Integer, primary_key=True, index=True)
    column_id = Column(Integer, ForeignKey("schemacolumn.id"), nullable=False)
    nl_term = Column(String(255), nullable=False, index=True)
    db_value = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    column = relationship("SchemaColumn", back_populates="value_mappings")
