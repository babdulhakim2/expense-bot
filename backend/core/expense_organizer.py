"""
Core expense organization logic - can be used by both API and Cloud Functions
"""
import logging
from typing import Dict, List, Any
from services.firebase_service import FirebaseService
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class ExpenseOrganizer:
    def __init__(self):
        self.firebase_service = FirebaseService()
        self.ai_service = AIService()
    
    def organize_all_users_expenses(self) -> Dict[str, Any]:
        """
        Main function to organize expenses for all users
        """
        try:
            logger.info("Starting expense organization for all users")
            
            # Get all users
            users = self._get_all_users()
            logger.info(f"Found {len(users)} users to process")
            
            results = []
            for user in users:
                try:
                    result = self.organize_user_expenses(user['id'])
                    results.append({
                        'user_id': user['id'],
                        'status': 'success',
                        'processed_count': result.get('processed_count', 0)
                    })
                    logger.info(f"Successfully processed user {user['id']}")
                except Exception as e:
                    logger.error(f"Failed to process user {user['id']}: {str(e)}")
                    results.append({
                        'user_id': user['id'],
                        'status': 'error',
                        'error': str(e)
                    })
            
            success_count = len([r for r in results if r['status'] == 'success'])
            error_count = len([r for r in results if r['status'] == 'error'])
            
            logger.info(f"Expense organization complete: {success_count} successful, {error_count} errors")
            
            return {
                'status': 'completed',
                'users_processed': len(users),
                'successful': success_count,
                'errors': error_count,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in expense organization: {str(e)}")
            raise
    
    def organize_user_expenses(self, user_id: str) -> Dict[str, Any]:
        """
        Organize expenses for a specific user
        """
        try:
            # Get user's unorganized expenses
            expenses_ref = self.firebase_service.db.collection('users').document(user_id).collection('expenses')
            unorganized_expenses = []
            
            for doc in expenses_ref.where('organized', '==', False).stream():
                expense_data = doc.to_dict()
                expense_data['id'] = doc.id
                unorganized_expenses.append(expense_data)
            
            logger.info(f"Found {len(unorganized_expenses)} unorganized expenses for user {user_id}")
            
            processed_count = 0
            for expense in unorganized_expenses:
                try:
                    organized_data = self._categorize_expense(expense)
                    
                    # Update the expense in Firestore
                    expense_ref = expenses_ref.document(expense['id'])
                    expense_ref.update({
                        'organized': True,
                        'category': organized_data.get('category'),
                        'processed_at': self.firebase_service.firestore.SERVER_TIMESTAMP,
                        'organization_metadata': organized_data.get('metadata', {})
                    })
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing expense {expense['id']}: {str(e)}")
            
            return {
                'processed_count': processed_count,
                'total_found': len(unorganized_expenses)
            }
            
        except Exception as e:
            logger.error(f"Error organizing expenses for user {user_id}: {str(e)}")
            raise
    
    def _get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from Firestore"""
        try:
            users_ref = self.firebase_service.db.collection('users')
            users = []
            for doc in users_ref.stream():
                users.append({
                    'id': doc.id,
                    'data': doc.to_dict()
                })
            return users
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return []
    
    def _categorize_expense(self, expense: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize expense using AI service
        """
        try:
            description = expense.get('description', '')
            amount = expense.get('amount', 0)
            
            # TODO: Use AI service here
            # category = self.ai_service.categorize_expense(description, amount)
            
            # For now, simple rule-based categorization
            category = self._simple_categorization(description)
            
            return {
                'category': category,
                'metadata': {
                    'auto_categorized': True,
                    'confidence': 'high',
                    'original_description': description,
                    'processed_by': 'expense_organizer'
                }
            }
        except Exception as e:
            logger.error(f"Error categorizing expense: {str(e)}")
            return {
                'category': 'miscellaneous',
                'metadata': {
                    'auto_categorized': False,
                    'error': str(e)
                }
            }
    
    def _simple_categorization(self, description: str) -> str:
        """Simple rule-based categorization"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['restaurant', 'food', 'cafe', 'dinner', 'lunch']):
            return 'food_dining'
        elif any(word in description_lower for word in ['gas', 'fuel', 'uber', 'taxi', 'transport']):
            return 'transportation'
        elif any(word in description_lower for word in ['store', 'shop', 'market', 'amazon']):
            return 'shopping'
        elif any(word in description_lower for word in ['rent', 'utilities', 'electric', 'water']):
            return 'housing'
        else:
            return 'miscellaneous'