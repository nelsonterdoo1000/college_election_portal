from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.db.models import Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import authenticate
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog
from .serializers import (
    UserSerializer, ElectionSerializer, PositionSerializer, CandidateSerializer,
    EligibleVoterSerializer, VoteSerializer, AuditLogSerializer, ElectionResultsSerializer
)
from .permissions import IsAdminOrReadOnly, IsEligibleVoter
from .utils import log_audit

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
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

class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all()
    serializer_class = ElectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.role == User.ADMIN:
            return Election.objects.all()
        return Election.objects.filter(eligible_voters__student=self.request.user)
    
    def perform_create(self, serializer):
        election = serializer.save(created_by=self.request.user)
        log_audit(self.request.user, 'create_election', f'Created election: {election.title}')
    
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
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        election = self.get_object()
        if election.status not in ['active', 'completed']:
            return Response(
                {'error': 'Results are only available for active or completed elections'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ElectionResultsSerializer(election)
        return Response(serializer.data)

class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return Position.objects.filter(election_id=self.kwargs['election_pk'])

class CandidateViewSet(viewsets.ModelViewSet):
    serializer_class = CandidateSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return Candidate.objects.filter(position_id=self.kwargs['position_pk'])

class VoteViewSet(viewsets.ModelViewSet):
    serializer_class = VoteSerializer
    permission_classes = [IsEligibleVoter]
    
    def get_queryset(self):
        return Vote.objects.filter(student=self.request.user)
    
    def create(self, request, *args, **kwargs):
        election_id = request.data.get('election')
        position_id = request.data.get('position')
        candidate_id = request.data.get('candidate')
        
        try:
            election = Election.objects.get(id=election_id)
            position = Position.objects.get(id=position_id)
            candidate = Candidate.objects.get(id=candidate_id)
            
            # Check if election is active
            if election.status != 'active':
                return Response(
                    {'error': 'Can only vote in active elections'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has already voted for this position
            existing_vote = Vote.objects.filter(
                election=election,
                position=position,
                student=request.user
            ).first()
            
            if existing_vote:
                # Update existing vote
                existing_vote.candidate = candidate
                existing_vote.save()
                vote = existing_vote
            else:
                # Create new vote
                vote = Vote.objects.create(
                    election=election,
                    position=position,
                    candidate=candidate,
                    student=request.user
                )
            
            # Broadcast updated results
            channel_layer = get_channel_layer()
            results = ElectionResultsSerializer(election).data
            async_to_sync(channel_layer.group_send)(
                f'election_{election_id}_results',
                {
                    'type': 'election_results_update',
                    'results': results
                }
            )
            
            return Response(self.get_serializer(vote).data)
            
        except (Election.DoesNotExist, Position.DoesNotExist, Candidate.DoesNotExist):
            return Response(
                {'error': 'Invalid election, position, or candidate'},
                status=status.HTTP_400_BAD_REQUEST
            )

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser] 