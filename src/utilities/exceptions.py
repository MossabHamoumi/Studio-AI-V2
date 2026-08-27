"""Studio-AI Custom Exceptions."""


class StudioAIError(Exception):
    """Base exception for all Studio-AI errors."""

    pass


class DatabaseError(StudioAIError):
    """Database connectivity or query execution error."""

    pass


class MigrationError(DatabaseError):
    """Schema migration failure."""

    pass


class ProjectNotFoundError(StudioAIError):
    """Requested project does not exist."""

    pass


class EntityNotFoundError(StudioAIError):
    """Generic entity not found error."""

    pass


class ValidationError(StudioAIError):
    """Input or entity validation failure."""

    pass


class JobStateError(StudioAIError):
    """Invalid job state transition error."""

    pass


class AssetNotFoundError(StudioAIError):
    """Referenced file asset not found or invalid."""

    pass


class WorkspaceError(StudioAIError):
    """Workspace filesystem operations error."""

    pass
