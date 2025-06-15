from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'elections', views.ElectionViewSet)
router.register(r'votes', views.VoteViewSet, basename='votes')
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-logs')

# Create nested routers for positions and candidates
elections_router = routers.NestedDefaultRouter(router, r'elections', lookup='election')
elections_router.register(r'positions', views.PositionViewSet, basename='election-positions')

positions_router = routers.NestedDefaultRouter(elections_router, r'positions', lookup='position')
positions_router.register(r'candidates', views.CandidateViewSet, basename='position-candidates')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/', include(elections_router.urls)),
    path('api/', include(positions_router.urls)),
] 