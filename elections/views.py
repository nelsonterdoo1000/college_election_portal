from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog
from .serializers import (
    UserSerializer, ElectionSerializer, PositionSerializer, CandidateSerializer,
    EligibleVoterSerializer, VoteSerializer, AuditLogSerializer, ElectionResultsSerializer
)
from .permissions import IsAdminOrReadOnly, IsEligibleVoter
from .utils import log_audit

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        if self.request.user.role == User.ADMIN:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

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
        if election.status != 'completed':
            return Response(
                {'error': 'Results are only available for completed elections'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ElectionResultsSerializer(election)
        return Response(serializer.data)

class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return Position.objects.filter(election_id=self.kwargs['election_pk'])

class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        return Candidate.objects.filter(position_id=self.kwargs['position_pk'])

class EligibleVoterViewSet(viewsets.ModelViewSet):
    queryset = EligibleVoter.objects.all()
    serializer_class = EligibleVoterSerializer
    permission_classes = [permissions.IsAdminUser]

class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [IsEligibleVoter]
    
    def perform_create(self, serializer):
        # Check if student has already voted for this position
        existing_vote = Vote.objects.filter(
            election=serializer.validated_data['election'],
            position=serializer.validated_data['position'],
            student=self.request.user
        ).exists()
        
        if existing_vote:
            raise serializers.ValidationError(
                'You have already voted for this position'
            )
        
        # Create the vote
        vote = serializer.save(student=self.request.user)
        
        # Update eligible voter status
        EligibleVoter.objects.filter(
            election=vote.election,
            student=self.request.user
        ).update(has_voted=True)
        
        # Log the vote
        log_audit(
            self.request.user,
            'cast_vote',
            f'Voted for {vote.candidate.name} in {vote.position.title}'
        )

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return AuditLog.objects.all().order_by('-timestamp') 