from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
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