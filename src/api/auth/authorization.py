"""Authorization helpers for resource access control."""
from typing import Protocol, Optional

from fastapi import HTTPException, status


class OwnedResource(Protocol):
    """Protocol for resources that have ownership."""
    created_by: str


def require_resource_owner(resource: OwnedResource, user_email: str) -> None:
    """
    Verify that the user owns the resource.
    
    Args:
        resource: Resource with created_by field
        user_email: Email of the authenticated user
        
    Raises:
        HTTPException: 403 Forbidden if user doesn't own the resource
    """
    if resource.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )


def require_resource_owner_or_fail(
    resource: Optional[OwnedResource],
    user_email: str,
    resource_type: str = "Resource"
) -> None:
    """
    Verify resource exists and user owns it.
    
    Args:
        resource: Resource to check (may be None)
        user_email: Email of the authenticated user
        resource_type: Type of resource for error message
        
    Raises:
        HTTPException: 404 if resource not found or not owned by user
    """
    if not resource or resource.created_by != user_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} not found"
        )
