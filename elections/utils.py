from .models import AuditLog

def log_audit(user, action, details):
    """
    Helper function to create audit log entries.
    
    Args:
        user: The user performing the action
        action: The type of action performed
        details: Additional details about the action
    """
    AuditLog.objects.create(
        user=user,
        action=action,
        details=details
    ) 