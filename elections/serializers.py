from rest_framework import serializers
from typing import List, Dict, Any
from .models import User, Election, Position, Candidate, EligibleVoter, Vote, AuditLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name', 'last_name']
        read_only_fields = ['role']

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'bio', 'photo', 'position']

class PositionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'election', 'candidates']

class ElectionSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_datetime', 'end_datetime', 
                 'status', 'created_by', 'positions']
        read_only_fields = ['status', 'created_by']

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'election', 'position', 'candidate', 'student', 'timestamp']
        read_only_fields = ['student', 'timestamp']

class ElectionResultsSerializer(serializers.ModelSerializer):
    positions = serializers.SerializerMethodField()
    
    class Meta:
        model = Election
        fields = ['id', 'title', 'positions']
    
    def get_positions(self, obj) -> List[Dict[str, Any]]:
        positions = Position.objects.filter(election=obj)
        result = []
        
        for position in positions:
            position_data = {
                'position_id': position.id,
                'position_title': position.title,
                'candidates': []
            }
            
            candidates = Candidate.objects.filter(position=position)
            for candidate in candidates:
                vote_count = Vote.objects.filter(
                    election=obj,
                    position=position,
                    candidate=candidate
                ).count()
                
                position_data['candidates'].append({
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.name,
                    'vote_count': vote_count
                })
            
            result.append(position_data)
        
        return result

class EligibleVoterSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = EligibleVoter
        fields = ['id', 'election', 'student']

class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'details', 'timestamp']

# New serializers for better user experience
class CandidateWithVoteStatusSerializer(serializers.ModelSerializer):
    has_voted_for = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = ['id', 'name', 'bio', 'photo', 'has_voted_for']
    
    def get_has_voted_for(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Check if user has voted for this candidate
        return Vote.objects.filter(
            election=obj.position.election,
            position=obj.position,
            candidate=obj,
            student=request.user
        ).exists()

class PositionWithVoteStatusSerializer(serializers.ModelSerializer):
    candidates = CandidateWithVoteStatusSerializer(many=True, read_only=True)
    user_has_voted = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'candidates', 'user_has_voted', 'user_vote']
    
    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Check if user has voted for this position
        return Vote.objects.filter(
            election=obj.election,
            position=obj,
            student=request.user
        ).exists()
    
    def get_user_vote(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Get the user's vote for this position
        vote = Vote.objects.filter(
            election=obj.election,
            position=obj,
            student=request.user
        ).first()
        
        if vote:
            return {
                'candidate_id': vote.candidate.id,
                'candidate_name': vote.candidate.name,
                'timestamp': vote.timestamp
            }
        return None

class ElectionWithVoteStatusSerializer(serializers.ModelSerializer):
    positions = PositionWithVoteStatusSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    user_is_eligible = serializers.SerializerMethodField()
    user_total_votes = serializers.SerializerMethodField()
    
    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_datetime', 'end_datetime', 
                 'status', 'created_by', 'positions', 'user_is_eligible', 'user_total_votes']
        read_only_fields = ['status', 'created_by']
    
    def get_user_is_eligible(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return EligibleVoter.objects.filter(
            election=obj,
            student=request.user
        ).exists()
    
    def get_user_total_votes(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        return Vote.objects.filter(
            election=obj,
            student=request.user
        ).count() 