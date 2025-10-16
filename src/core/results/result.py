"""Result pattern implementation for clean error handling."""
from typing import Generic, TypeVar, Optional, List
from dataclasses import dataclass
from .validation_error import ValidationError

T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """
    Result pattern for explicit success/failure handling without exceptions.

    This pattern ensures that all business rule violations and failures
    are handled explicitly rather than through exceptions.
    """

    _value: Optional[T] = None
    _error: Optional[str] = None
    _validation_errors: Optional[List[ValidationError]] = None
    _is_success: bool = False

    @property
    def is_success(self) -> bool:
        """Returns True if the operation was successful."""
        return self._is_success

    @property
    def is_failure(self) -> bool:
        """Returns True if the operation failed."""
        return not self._is_success

    @property
    def value(self) -> Optional[T]:
        """Returns the value if successful, None otherwise."""
        if self.is_failure:
            raise ValueError("Cannot access value of a failed result")
        return self._value

    @property
    def error(self) -> Optional[str]:
        """Returns the error message if failed, None otherwise."""
        return self._error

    @property
    def validation_errors(self) -> Optional[List[ValidationError]]:
        """Returns validation errors if any, None otherwise."""
        return self._validation_errors

    @staticmethod
    def success(value: T) -> 'Result[T]':
        """Creates a successful result with a value."""
        return Result(_value=value, _is_success=True)

    @staticmethod
    def failure(error: str) -> 'Result[T]':
        """Creates a failed result with an error message."""
        return Result(_error=error, _is_success=False)

    @staticmethod
    def validation_failure(errors: List[ValidationError]) -> 'Result[T]':
        """Creates a failed result with validation errors."""
        error_messages = "; ".join(str(e) for e in errors)
        return Result(
            _error=f"Validation failed: {error_messages}",
            _validation_errors=errors,
            _is_success=False
        )

    def __bool__(self) -> bool:
        """Allows using Result in boolean context."""
        return self.is_success

    def __repr__(self) -> str:
        """String representation of the result."""
        if self.is_success:
            return f"Result.Success({self._value})"
        elif self._validation_errors:
            return f"Result.ValidationFailure({len(self._validation_errors)} errors)"
        else:
            return f"Result.Failure({self._error})"
