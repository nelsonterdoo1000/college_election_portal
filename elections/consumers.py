import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Election, Position, Candidate, Vote

class ElectionResultsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.election_id = self.scope['url_route']['kwargs']['election_id']
        self.room_group_name = f'election_{self.election_id}_results'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial results
        initial_results = await self.get_election_results()
        await self.send(text_data=json.dumps(initial_results))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        # Handle any incoming messages if needed
        pass
    
    async def election_results_update(self, event):
        # Send updated results to WebSocket
        results = event['results']
        await self.send(text_data=json.dumps(results))
    
    @database_sync_to_async
    def get_election_results(self):
        try:
            election = Election.objects.get(id=self.election_id)
            positions = Position.objects.filter(election=election)
            
            results = {
                'election_id': election.id,
                'election_title': election.title,
                'positions': []
            }
            
            for position in positions:
                position_data = {
                    'position_id': position.id,
                    'position_title': position.title,
                    'candidates': []
                }
                
                candidates = Candidate.objects.filter(position=position)
                for candidate in candidates:
                    vote_count = Vote.objects.filter(
                        election=election,
                        position=position,
                        candidate=candidate
                    ).count()
                    
                    position_data['candidates'].append({
                        'candidate_id': candidate.id,
                        'candidate_name': candidate.name,
                        'vote_count': vote_count
                    })
                
                results['positions'].append(position_data)
            
            return results
        except Election.DoesNotExist:
            return {'error': 'Election not found'} 