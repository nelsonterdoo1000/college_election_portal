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