from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib import messages
from django.db import transaction
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog
from .utils import log_audit

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'student_id', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'student_id', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'student_id')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'student_id')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'student_id', 'role', 'password1', 'password2'),
        }),
    )
    
    actions = ['make_eligible_voters_for_active_election']
    
    def make_eligible_voters_for_active_election(self, request, queryset):
        """Make selected users eligible voters for the first active election"""
        # Get the first active election
        election = Election.objects.filter(status='active').first()
        
        if not election:
            # If no active election, get the first upcoming election
            election = Election.objects.filter(status='upcoming').first()
        
        if not election:
            # If no active or upcoming election, get the first election
            election = Election.objects.first()
        
        if not election:
            self.message_user(request, 'No elections available.', level=messages.ERROR)
            return
        
        # Get existing eligible voters for this election
        existing_eligible_voters = set(
            EligibleVoter.objects.filter(election=election).values_list('student_id', flat=True)
        )
        
        # Filter out users who are already eligible
        new_eligible_user_ids = set(queryset.values_list('id', flat=True)) - existing_eligible_voters
        
        # Create EligibleVoter records for new users
        eligible_voters_to_create = []
        for user_id in new_eligible_user_ids:
            eligible_voters_to_create.append(
                EligibleVoter(election=election, student_id=user_id)
            )
        
        if eligible_voters_to_create:
            with transaction.atomic():
                EligibleVoter.objects.bulk_create(eligible_voters_to_create)
                
                # Log the bulk operation
                log_audit(
                    request.user, 
                    'bulk_add_eligible_voters', 
                    f'Added {len(eligible_voters_to_create)} eligible voters to election: {election.title}'
                )
            
            skipped_count = len(queryset) - len(new_eligible_user_ids)
            self.message_user(
                request, 
                f'Successfully added {len(eligible_voters_to_create)} users as eligible voters for {election.title}. '
                f'Skipped {skipped_count} users who were already eligible.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                f'All selected users are already eligible voters for {election.title}.',
                level=messages.WARNING
            )
    
    make_eligible_voters_for_active_election.short_description = "Make selected users eligible voters for active election"

class PositionInline(admin.TabularInline):
    model = Position
    extra = 1

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'start_datetime', 'end_datetime', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_datetime'
    inlines = [PositionInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election', 'order')
    list_filter = ('election',)
    search_fields = ('title', 'description')
    inlines = [CandidateInline]

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'order')
    list_filter = ('position__election', 'position')
    search_fields = ('name', 'bio')

@admin.register(EligibleVoter)
class EligibleVoterAdmin(admin.ModelAdmin):
    list_display = ('student', 'election', 'has_voted')
    list_filter = ('election', 'has_voted')
    search_fields = ('student__username', 'student__email', 'student__student_id')
    actions = ['remove_eligible_voters']
    
    def remove_eligible_voters(self, request, queryset):
        """Remove selected eligible voters"""
        if not queryset.exists():
            self.message_user(request, 'No eligible voters selected.', level=messages.WARNING)
            return
        
        # Get the election from the first selected eligible voter
        # This assumes all selected eligible voters are from the same election
        election = queryset.first().election
        
        # Delete eligible voter records
        deleted_count, _ = queryset.delete()
        
        if deleted_count > 0:
            # Log the bulk operation
            log_audit(
                request.user, 
                'bulk_remove_eligible_voters', 
                f'Removed {deleted_count} eligible voters from election: {election.title}'
            )
            
            self.message_user(
                request, 
                f'Successfully removed {deleted_count} users from eligible voters for {election.title}.',
                level=messages.SUCCESS
            )
        else:
            self.message_user(
                request, 
                f'No eligible voters were removed.',
                level=messages.WARNING
            )
    
    remove_eligible_voters.short_description = "Remove selected eligible voters"

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('election', 'position', 'candidate', 'timestamp')
    list_filter = ('election', 'position', 'timestamp')
    search_fields = ('candidate__name',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Votes can only be created through the API

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp', 'ip_address')
    list_filter = ('timestamp', 'user')
    search_fields = ('action', 'user__username')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'action', 'details', 'timestamp', 'ip_address')
    
    def has_add_permission(self, request):
        return False  # Audit logs can only be created through the system 