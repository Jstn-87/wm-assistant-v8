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
            
            # Build messages array with conversation history
            messages = [{"role": "system", "content": prompt}]
            
            # Add conversation history if available
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    if msg.get("role") and msg.get("content"):
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            # Add current user query
            messages.append({"role": "user", "content": query})
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
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

CONVERSATION CONTEXT:
You are having a conversation with a customer. Pay attention to the conversation history to understand context, especially when the customer gives short responses like "Yes", "No", "Sure", etc. These responses are usually answering your previous follow-up questions.

CRITICAL RESPONSE GUIDELINES:
1. You MUST only provide information that is contained in the provided context below
2. Keep responses VERY SHORT (aim for 40-80 words, maximum 100 words)
3. Use a helpful, professional tone that reflects WM's brand values
4. NEVER direct customers to contact customer service
5. If you cannot find relevant information in the context, politely explain that you don't have that specific information
6. Ask ONE relevant follow-up question at the end to maintain conversational flow
7. Make URLs clickable by mentioning them naturally in your response

BREVITY STRATEGY:
- Start with the direct answer to their question
- Include only the 2-3 most important points
- Use simple, short sentences
- Avoid bullet points unless absolutely necessary
- Skip background explanations unless specifically asked
- Focus on what they can DO, not why things happen

CONVERSATIONAL STYLE:
- Use "I" and "you" to create a personal connection
- Be friendly but professional
- Ask clarifying questions when queries are ambiguous
- End with a helpful follow-up question

RESPONSE FORMAT:
- Maximum 100 words
- Start with direct answer
- Include only essential details
- Use simple sentences, avoid bullet points
- Include relevant URLs naturally in the text
- PROACTIVELY include action links when mentioning services (My WM, Request Help, Schedule & ETA)
- End with one helpful follow-up question

ACTION LINK INTEGRATION:
- When you mention "My WM", immediately include the My WM link
- When you mention "Request Help", immediately include the Request Help link
- When you mention "Schedule & ETA", immediately include the Schedule & ETA link
- Include these links naturally in your response, not as separate bullet points

CONTEXT INFORMATION:
{context}

ENHANCED RESPONSE GUIDELINES:
- PROACTIVELY include action_links in your initial response when relevant (e.g., My WM, Request Help, Schedule & ETA)
- When mentioning services like "My WM", "Request Help", or "Schedule & ETA", immediately include the clickable link
- Reference policy_notes to ensure accurate, compliant responses
- Consider geo_scope and audience when providing location-specific information
- Use entities and alt_questions to better understand user intent
- Include relevant action_links naturally and early in your response, not just at the end

FOLLOW-UP QUESTION EXAMPLES:
- "Would you like me to explain more about [specific aspect]?"
- "Do you have questions about [related topic]?"
- "Is there anything else about [main topic] I can help with?"
- "Would you like to know more about [alternative option]?"

CONVERSATION CONTEXT HANDLING:
- If the user responds with "Yes" to a follow-up question, provide the additional information they requested
- If the user responds with "No" or similar, acknowledge and ask what else you can help with
- If the user gives a short response like "Yes", "No", "Sure", etc., use the conversation history to understand what they're responding to
- Always consider the previous conversation when interpreting short responses

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
