from rest_framework import permissions
from .models import EligibleVoter

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users
        return request.user and request.user.role == 'admin'

class IsEligibleVoter(permissions.BasePermission):
    """
    Custom permission to only allow eligible voters to vote.
    """
    def has_permission(self, request, view):
        # Only allow students to vote
        if not request.user or request.user.role != 'student':
            return False

        # For POST requests (voting), check if user is eligible for the election
        if request.method == 'POST':
            election_id = request.data.get('election')
            if not election_id:
                return False

            try:
                # Check if user is eligible for this election
                # Note: We don't check has_voted here because users can vote for multiple positions
                EligibleVoter.objects.get(
                    election_id=election_id,
                    student=request.user
                )
                return True
            except EligibleVoter.DoesNotExist:
                return False

        # Allow GET requests for viewing votes
        return request.method in permissions.SAFE_METHODS

class IsStudentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'student' 