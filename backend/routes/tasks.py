"""
Task endpoints for scheduled jobs
"""
from flask import Blueprint, request, jsonify
import logging
from services.firebase_service import FirebaseService
from services.ai_service import AIService
from datetime import datetime

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

# Initialize services
firebase_service = FirebaseService()
ai_service = AIService()

@tasks_bp.route('/organize-expenses', methods=['POST'])
def organize_expenses():
    """
    Endpoint called by Cloud Scheduler to organize expenses
    """
    try:
        # Verify the request is from Cloud Scheduler (optional)
        # You can check headers or add auth here
        
        logger.info("Starting scheduled expense organization")
        
        # Get all users
        users_ref = firebase_service.db.collection('users')
        users = []
        for doc in users_ref.stream():
            users.append({
                'id': doc.id,
                'data': doc.to_dict()
            })
        
        logger.info(f"Processing {len(users)} users")
        
        # Process each user
        results = []
        for user in users:
            try:
                result = organize_user_expenses(user['id'])
                results.append({
                    'user_id': user['id'],
                    'status': 'success',
                    'processed': result
                })
            except Exception as e:
                logger.error(f"Error processing user {user['id']}: {str(e)}")
                results.append({
                    'user_id': user['id'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'users_processed': len(users),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in expense organization task: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

def organize_user_expenses(user_id: str) -> dict:
    """
    Organize expenses for a specific user
    """
    # Implementation here - reuse your existing logic
    # Can call AI service, update Firestore, etc.
    return {'processed_count': 0}  # placeholder

@tasks_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for task endpoints"""
    return jsonify({'status': 'healthy'}), 200