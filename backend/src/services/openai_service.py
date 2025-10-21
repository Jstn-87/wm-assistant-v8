"""
OpenAI service for WM Assistant.
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import OpenAI
from ..config import get_settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the OpenAI service."""
        try:
            logger.info("Initializing OpenAI service...")
            
            # Initialize OpenAI client
            self.client = OpenAI(api_key=self.settings.openai_api_key)
            
            # Test the connection
            if self.settings.openai_api_key == "test-key-for-development":
                logger.warning("Using test API key - OpenAI calls will be mocked")
                self._initialized = True
                return True
            
            # Test with a simple request
            try:
                response = self.client.models.list()
                logger.info("OpenAI service initialized successfully")
                self._initialized = True
                return True
            except Exception as e:
                logger.error(f"OpenAI API test failed: {e}")
                # Don't fail initialization for API key issues - we'll handle it in the response generation
                logger.warning("Continuing with OpenAI service despite API test failure")
                self._initialized = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """Check if the OpenAI service is initialized."""
        return self._initialized
    
    def generate_response(
        self, 
        query: str, 
        context: str, 
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate a response using OpenAI API with RAG context."""
        if not self._initialized:
            return {
                "content": "I'm sorry, but I'm currently unable to process your request. Please try again later.",
                "error": "OpenAI service not initialized"
            }
        
        start_time = time.time()
        
        try:
            # Build the prompt
            prompt = self._build_prompt(query, context, conversation_history)
            
            # Use test response if using test key
            if self.settings.openai_api_key == "test-key-for-development":
                return self._generate_test_response(query, context, start_time)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ],
                max_tokens=self.settings.openai_max_tokens,
                temperature=0.7
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "content": response.choices[0].message.content.strip(),
                "response_time_ms": response_time_ms,
                "model": self.settings.openai_model,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                "error": str(e),
                "response_time_ms": response_time_ms
            }
    
    def _build_prompt(self, query: str, context: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Build the system prompt for OpenAI."""
        prompt = """You are the WM Assistant, an AI-powered customer support chatbot for Waste Management (WM). Your role is to provide helpful, accurate, and conversational responses to customer queries.

IMPORTANT GUIDELINES:
1. You MUST only provide information that is contained in the provided context below
2. Keep responses concise and conversational (under 200 words)
3. Use a helpful, professional tone that reflects WM's brand values
4. NEVER direct customers to contact customer service
5. If you cannot find relevant information in the context, politely explain that you don't have that specific information
6. Ask relevant follow-up questions when appropriate to maintain conversational flow
7. Make URLs clickable by mentioning them naturally in your response

CONVERSATIONAL STYLE:
- Use "I" and "you" to create a personal connection
- Be friendly but professional
- Break down complex information into digestible parts
- Ask clarifying questions when queries are ambiguous

RESPONSE FORMAT:
- Keep responses under 200 words
- Use bullet points or numbered lists when helpful
- Include relevant URLs naturally in the text
- End with a helpful follow-up question when appropriate

CONTEXT INFORMATION:
{context}

Remember: Only use information from the context above. If the context doesn't contain relevant information, politely explain that you don't have that specific information available."""

        return prompt.format(context=context if context else "No relevant context found.")
    
    def _generate_test_response(self, query: str, context: str, start_time: float) -> Dict[str, Any]:
        """Generate a test response when using test API key."""
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Simple test response based on query content
        if "moving" in query.lower() or "transfer" in query.lower():
            content = """I can help you with transferring your WM service when moving! 

To transfer your service, you'll need to provide:
• Your moving date
• Your new address  
• When you'd like service to start at your new address

You can transfer your service online through My WM. Would you like me to walk you through the online transfer process?"""
        elif "dumpster" in query.lower() or "materials" in query.lower():
            content = """I can help you understand what materials are allowed in your dumpster!

Here are some items that are NOT allowed:
• Aerosol cans
• All liquids
• Appliances
• Batteries
• Hazardous waste
• Paint (except dried latex paint cans)

Would you like me to provide a complete list of prohibited materials?"""
        elif "billing" in query.lower() or "bill" in query.lower():
            content = """I can help you with billing questions!

You can view your current bill and manage your account through My WM. If you need a quick way to access your invoice, you can use the "Request Help" button on our support page.

What specific billing question can I help you with today?"""
        else:
            content = f"""I understand you're asking about: "{query}"

I'm here to help with WM services including:
• Service changes and transfers
• Container guidelines
• Billing questions
• Recycling information
• Additional services

Could you provide more details about what you need help with?"""
        
        return {
            "content": content,
            "response_time_ms": response_time_ms,
            "model": "test-model",
            "tokens_used": len(content.split()) * 1.3  # Rough estimate
        }
    
    def validate_api_key(self) -> bool:
        """Validate the OpenAI API key."""
        if self.settings.openai_api_key == "test-key-for-development":
            return True
        
        try:
            response = self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (placeholder for future implementation)."""
        return {
            "model": self.settings.openai_model,
            "max_tokens": self.settings.openai_max_tokens,
            "initialized": self._initialized
        }
