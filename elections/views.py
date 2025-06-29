from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.db.models import Count
from asgiref.sync import async_to_sync
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog
from .serializers import (
    UserSerializer, ElectionSerializer, PositionSerializer, CandidateSerializer,
    EligibleVoterSerializer, VoteSerializer, AuditLogSerializer, ElectionResultsSerializer
)
from .permissions import IsAdminOrReadOnly, IsEligibleVoter
from .utils import log_audit
from django.http import JsonResponse

# Handle channels import gracefully
try:
    from channels.layers import get_channel_layer
except ImportError:
    # Fallback for older versions
    from channels import get_channel_layer

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['authentication'],
        summary="User Login",
        description="Authenticate user and return JWT tokens for API access",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string', 'description': 'User username'},
                    'password': {'type': 'string', 'description': 'User password'},
                },
                'required': ['username', 'password']
            }
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                    'access': {'type': 'string', 'description': 'JWT access token'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'role': {'type': 'string'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                        }
                    }
                }
            },
            401: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Invalid credentials'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Successful Login',
                value={
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    'user': {
                        'id': 1,
                        'username': 'student1',
                        'email': 'student1@college.edu',
                        'role': 'student',
                        'first_name': 'John',
                        'last_name': 'Doe'
                    }
                },
                status_codes=['200']
            ),
            OpenApiExample(
                'Invalid Credentials',
                value={'error': 'Invalid credentials'},
                status_codes=['401']
            )
        ]
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutView(APIView):
    @extend_schema(
        tags=['authentication'],
        summary="User Logout",
        description="Logout user and blacklist refresh token",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string', 'description': 'JWT refresh token to blacklist'},
                },
                'required': ['refresh']
            }
        },
        responses={
            205: {
                'description': 'Successfully logged out'
            }
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        tags=['users'],
        summary="List Users",
        description="Get a list of all users (Admin only)",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Create User",
        description="Create a new user (Admin only)",
        responses={201: UserSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Get User Details",
        description="Get detailed information about a specific user",
        responses={200: UserSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    @extend_schema(
        tags=['elections'],
        summary="List Elections",
        description="Get a list of elections. Admins see all elections, students see only their eligible elections.",
        responses={200: ElectionSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['elections'],
        summary="Create Election",
        description="Create a new election (Admin only)",
        responses={201: ElectionSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['elections'],
        summary="Get Election Details",
        description="Get detailed information about a specific election",
        responses={200: ElectionSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        if self.request.user.role == User.ADMIN:
            return Election.objects.all()
        return Election.objects.filter(eligible_voters__student=self.request.user)
    
    def perform_create(self, serializer):
        election = serializer.save(created_by=self.request.user)
        log_audit(self.request.user, 'create_election', f'Created election: {election.title}')
    
    @extend_schema(
        tags=['elections'],
        summary="Start Election",
        description="Start an election by changing its status from 'pending' to 'active' (Admin only)",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'description': 'Confirmation message'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        election = self.get_object()
        if election.status != 'pending':
            return Response(
                {'error': 'Only pending elections can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election.status = 'active'
        election.save()
        log_audit(request.user, 'start_election', f'Started election: {election.title}')
        return Response({'status': 'election started'})
    
    @extend_schema(
        tags=['elections'],
        summary="End Election",
        description="End an election by changing its status from 'active' to 'completed' (Admin only)",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'description': 'Confirmation message'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                }
            }
        }
    )
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        election = self.get_object()
        if election.status != 'active':
            return Response(
                {'error': 'Only active elections can be ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election.status = 'completed'
        election.save()
        log_audit(request.user, 'end_election', f'Ended election: {election.title}')
        return Response({'status': 'election ended'})

class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    @extend_schema(
        tags=['positions'],
        summary="List Positions",
        description="Get a list of positions for a specific election",
        parameters=[
            OpenApiParameter(
                name='election_pk',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={200: PositionSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['positions'],
        summary="Create Position",
        description="Create a new position for an election (Admin only)",
        parameters=[
            OpenApiParameter(
                name='election_pk',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={201: PositionSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['positions'],
        summary="Get Position Details",
        description="Get detailed information about a specific position",
        parameters=[
            OpenApiParameter(
                name='election_pk',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='id',
                location=OpenApiParameter.PATH,
                description='ID of the position',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={200: PositionSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        return Position.objects.filter(election_id=self.kwargs['election_pk'])

class CandidateViewSet(viewsets.ModelViewSet):
    serializer_class = CandidateSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    @extend_schema(
        tags=['candidates'],
        summary="List Candidates",
        description="Get a list of candidates for a specific position",
        parameters=[
            OpenApiParameter(
                name='election_pk',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='position_pk',
                location=OpenApiParameter.PATH,
                description='ID of the position',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={200: CandidateSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['candidates'],
        summary="Create Candidate",
        description="Add a new candidate to a position (Admin only)",
        parameters=[
            OpenApiParameter(
                name='election_pk',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='position_pk',
                location=OpenApiParameter.PATH,
                description='ID of the position',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={201: CandidateSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['candidates'],
        summary="Get Candidate Details",
        description="Get detailed information about a specific candidate",
        parameters=[
            OpenApiParameter(
                name='election_pk',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='position_pk',
                location=OpenApiParameter.PATH,
                description='ID of the position',
                required=True,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='id',
                location=OpenApiParameter.PATH,
                description='ID of the candidate',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={200: CandidateSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        return Candidate.objects.filter(position_id=self.kwargs['position_pk'])

class VoteViewSet(viewsets.ModelViewSet):
    serializer_class = VoteSerializer
    permission_classes = [IsEligibleVoter]
    
    @extend_schema(
        tags=['voting'],
        summary="List User's Votes",
        description="Get a list of votes cast by the authenticated user",
        responses={200: VoteSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['voting'],
        summary="Get Vote Details",
        description="Get detailed information about a specific vote",
        parameters=[
            OpenApiParameter(
                name='id',
                location=OpenApiParameter.PATH,
                description='ID of the vote',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={200: VoteSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['voting'],
        summary="Cast a Vote",
        description="Cast a vote for a candidate in an election (Students only, one vote per position)",
        request=VoteSerializer,
        responses={
            201: VoteSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                }
            }
        }
    )
    def create(self, request, *args, **kwargs):
        election_id = request.data.get('election')
        position_id = request.data.get('position')
        candidate_id = request.data.get('candidate')
        
        # Check if user has already voted for this position in this election
        existing_vote = Vote.objects.filter(
            election_id=election_id,
            position_id=position_id,
            student=request.user
        ).first()
        
        if existing_vote:
            return Response(
                {'error': 'You have already voted for this position in this election'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the vote
        vote = Vote.objects.create(
            election_id=election_id,
            position_id=position_id,
            candidate_id=candidate_id,
            student=request.user
        )
        
        # Mark user as having voted
        eligible_voter = EligibleVoter.objects.get(
            election_id=election_id,
            student=request.user
        )
        eligible_voter.has_voted = True
        eligible_voter.save()
        
        # Log the vote
        log_audit(request.user, 'cast_vote', f'Voted for candidate {vote.candidate.name} in {vote.position.title}')
        
        # Send real-time update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'election_{election_id}',
            {
                'type': 'election_results_update',
                'election_id': election_id
            }
        )
        
        serializer = self.get_serializer(vote)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_queryset(self):
        return Vote.objects.filter(student=self.request.user)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        tags=['audit'],
        summary="List Audit Logs",
        description="Get a list of audit log entries (Admin only)",
        responses={200: AuditLogSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['audit'],
        summary="Get Audit Log Details",
        description="Get detailed information about a specific audit log entry",
        responses={200: AuditLogSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class ElectionResultsView(APIView):
    """
    Dedicated view for getting election results - easily discoverable in Swagger
    """
    permission_classes = [permissions.AllowAny]  # Public endpoint
    
    @extend_schema(
        tags=['elections'],
        summary="Get Election Results",
        description="Get real-time results for an active or completed election (Public endpoint - no authentication required)",
        parameters=[
            OpenApiParameter(
                name='election_id',
                location=OpenApiParameter.PATH,
                description='ID of the election',
                required=True,
                type=OpenApiTypes.INT
            )
        ],
        responses={
            200: ElectionResultsSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                }
            },
            404: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Election not found'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Successful Results',
                value={
                    'id': 1,
                    'title': 'Student Council Election 2024',
                    'positions': [
                        {
                            'position_id': 1,
                            'position_title': 'President',
                            'candidates': [
                                {
                                    'candidate_id': 1,
                                    'candidate_name': 'John Doe',
                                    'vote_count': 45
                                },
                                {
                                    'candidate_id': 2,
                                    'candidate_name': 'Jane Smith',
                                    'vote_count': 38
                                }
                            ]
                        }
                    ]
                },
                status_codes=['200']
            ),
            OpenApiExample(
                'Election Not Active',
                value={'error': 'Results are only available for active or completed elections'},
                status_codes=['400']
            )
        ]
    )
    def get(self, request, election_id):
        try:
            election = Election.objects.get(id=election_id)
            if election.status not in ['active', 'completed']:
                return Response(
                    {'error': 'Results are only available for active or completed elections'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = ElectionResultsSerializer(election)
            return Response(serializer.data)
        except Election.DoesNotExist:
            return Response(
                {'detail': 'Election not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class PublicElectionsView(APIView):
    """
    Public endpoint to list active and completed elections for unauthenticated users
    """
    permission_classes = [permissions.AllowAny]  # Public endpoint
    
    @extend_schema(
        tags=['elections'],
        summary="List Public Elections",
        description="Get a list of active and completed elections (Public endpoint - no authentication required)",
        responses={
            200: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'description': 'Election ID'},
                        'title': {'type': 'string', 'description': 'Election title'},
                        'description': {'type': 'string', 'description': 'Election description'},
                        'status': {'type': 'string', 'description': 'Election status'},
                        'start_datetime': {'type': 'string', 'format': 'date-time'},
                        'end_datetime': {'type': 'string', 'format': 'date-time'},
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Public Elections List',
                value=[
                    {
                        'id': 1,
                        'title': 'Student Council Election 2024',
                        'description': 'Annual student council election',
                        'status': 'active',
                        'start_datetime': '2024-03-01T09:00:00Z',
                        'end_datetime': '2024-03-01T17:00:00Z'
                    },
                    {
                        'id': 2,
                        'title': 'Class Representative Election 2024',
                        'description': 'Class representative election',
                        'status': 'completed',
                        'start_datetime': '2024-02-15T09:00:00Z',
                        'end_datetime': '2024-02-15T17:00:00Z'
                    }
                ],
                status_codes=['200']
            )
        ]
    )
    def get(self, request):
        # Only show active and completed elections to the public
        elections = Election.objects.filter(
            status__in=['active', 'completed']
        ).values('id', 'title', 'description', 'status', 'start_datetime', 'end_datetime')
        
        return Response(list(elections))

def api_root(request):
    return JsonResponse({"message": "Welcome to the College Election API."}) 