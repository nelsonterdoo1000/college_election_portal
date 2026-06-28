from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib import messages
from django.db import transaction
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.utils import timezone
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.conf import settings
from django_q.tasks import async_task
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog, OTPVerification
from .utils import log_audit

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'student_id', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User

class UserResource(resources.ModelResource):
    class Meta:
        model = User
        import_id_fields = ('email',)
        fields = ('email', 'first_name', 'last_name', 'username', 'role', 'is_active')
        exclude = ('password',)

    def before_import_row(self, row, **kwargs):
        email = str(row.get('email', '')).strip().lower()
        full_name = str(row.get('full_name', '')).strip()
        
        row['email'] = email
        row['username'] = email
        row['is_active'] = True
        row['role'] = 'student'
        
        # Parse full_name: expected format 'Last First Second'
        if full_name and 'first_name' not in row:
            name_parts = full_name.split()
            last_name = name_parts[0] if len(name_parts) > 0 else ''
            first_name = name_parts[1] if len(name_parts) > 1 else ''
            if len(name_parts) > 2:
                first_name += " " + " ".join(name_parts[2:])
            row['first_name'] = first_name
            row['last_name'] = last_name

    def after_save_instance(self, instance, row, **kwargs):
        # Only send emails if this is the actual import, not a dry-run preview
        dry_run = kwargs.get('dry_run', False)
        if not dry_run:
            async_task('elections.tasks.send_password_reset_email', instance.id, task_name=instance.email)

@admin.register(User)
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = UserResource
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

class ElectionResource(resources.ModelResource):
    class Meta:
        model = Election

@admin.register(Election)
class ElectionAdmin(ImportExportModelAdmin):
    resource_class = ElectionResource
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

class PositionResource(resources.ModelResource):
    class Meta:
        model = Position

@admin.register(Position)
class PositionAdmin(ImportExportModelAdmin):
    resource_class = PositionResource
    list_display = ('title', 'election', 'order')
    list_filter = ('election',)
    search_fields = ('title', 'description')
    inlines = [CandidateInline]

class CandidateResource(resources.ModelResource):
    class Meta:
        model = Candidate

@admin.register(Candidate)
class CandidateAdmin(ImportExportModelAdmin):
    resource_class = CandidateResource
    list_display = ('name', 'position', 'order')
    list_filter = ('position__election', 'position')
    search_fields = ('name', 'bio')

class EligibleVoterResource(resources.ModelResource):
    class Meta:
        model = EligibleVoter

@admin.register(EligibleVoter)
class EligibleVoterAdmin(ImportExportModelAdmin):
    resource_class = EligibleVoterResource
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

class VoteResource(resources.ModelResource):
    class Meta:
        model = Vote

@admin.register(Vote)
class VoteAdmin(ImportExportModelAdmin):
    resource_class = VoteResource
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

from django.contrib.admin.models import LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_time', 'user', 'content_type', 'action_flag')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'
    readonly_fields = ('user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message', 'action_time')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False