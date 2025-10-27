from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.ValueMapping])
def read_value_mappings(
    db: Session = Depends(deps.get_db),
    column_id: int = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve value mappings, optionally filtered by column.
    """
    if column_id:
        mappings = crud.value_mapping.get_by_column(db=db, column_id=column_id, skip=skip, limit=limit)
    else:
        mappings = crud.value_mapping.get_multi(db=db, skip=skip, limit=limit)
    return mappings


@router.post("/", response_model=schemas.ValueMapping)
def create_value_mapping(
    *,
    db: Session = Depends(deps.get_db),
    mapping_in: schemas.ValueMappingCreate,
) -> Any:
    """
    Create new value mapping.
    """
    # Check if column exists
    column = crud.schema_column.get(db=db, id=mapping_in.column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")
    
    # Check if mapping already exists
    existing = crud.value_mapping.get_by_column_and_term(
        db=db, 
        column_id=mapping_in.column_id, 
        nl_term=mapping_in.nl_term
    )
    if existing:
        raise HTTPException(status_code=400, detail="Mapping already exists for this term")
    
    mapping = crud.value_mapping.create(db=db, obj_in=mapping_in)
    return mapping


@router.get("/{mapping_id}", response_model=schemas.ValueMapping)
def read_value_mapping(
    *,
    db: Session = Depends(deps.get_db),
    mapping_id: int,
) -> Any:
    """
    Get value mapping by ID.
    """
    mapping = crud.value_mapping.get(db=db, id=mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Value mapping not found")
    return mapping


@router.put("/{mapping_id}", response_model=schemas.ValueMapping)
def update_value_mapping(
    *,
    db: Session = Depends(deps.get_db),
    mapping_id: int,
    mapping_in: schemas.ValueMappingUpdate,
) -> Any:
    """
    Update a value mapping.
    """
    mapping = crud.value_mapping.get(db=db, id=mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Value mapping not found")
    
    # Check if new term would create a duplicate
    if mapping_in.nl_term and mapping_in.nl_term != mapping.nl_term:
        existing = crud.value_mapping.get_by_column_and_term(
            db=db, 
            column_id=mapping.column_id, 
            nl_term=mapping_in.nl_term
        )
        if existing:
            raise HTTPException(status_code=400, detail="Mapping already exists for this term")
    
    mapping = crud.value_mapping.update(db=db, db_obj=mapping, obj_in=mapping_in)
    return mapping


@router.delete("/{mapping_id}", response_model=schemas.ValueMapping)
def delete_value_mapping(
    *,
    db: Session = Depends(deps.get_db),
    mapping_id: int,
) -> Any:
    """
    Delete a value mapping.
    """
    mapping = crud.value_mapping.get(db=db, id=mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Value mapping not found")
    mapping = crud.value_mapping.remove(db=db, id=mapping_id)
    return mapping
