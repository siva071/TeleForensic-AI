def get_ai_response(user_message, file_context, findings_text, scores_text, chat_history, api_key):
    """Get AI response from Gemini API"""
    try:
        import google.generativeai as genai
        
        # Configure API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Detect if user is asking about IPDR specifically
        user_message_lower = user_message.lower()
        is_ipdr_query = 'ipdr' in user_message_lower
        
        # Build system context
        if is_ipdr_query:
            system_context = f"""You are TeleForensic AI, expert AI investigation assistant for police telecom forensic analysis.

RULES:
- Respond in SAME LANGUAGE user types
- Telugu input → Telugu response
- Hindi → Hindi, Kannada → Kannada
- English → English
- Base answers only on provided IPDR data
- Focus on IPDR analysis: IP addresses, URLs, data usage, protocols, VPN usage
- Always suggest investigation leads for IPDR data
- For non-investigation questions say: I am TeleForensic AI focused only on telecom forensic analysis

UPLOADED IPDR FILE DATA:
{file_context}

PATTERN ANALYSIS:
{findings_text}

SUSPICION SCORES:
{scores_text}

CHAT HISTORY:
{chat_history}

INVESTIGATOR QUESTION: {user_message}

IMPORTANT: Analyze the IPDR data specifically. Look for:
- Suspicious IP addresses and their frequency
- VPN/proxy usage (vpngate.net, tor, etc.)
- Encrypted messaging apps (telegram.org, whatsapp.com, signal)
- Dark web or suspicious URLs
- Unusual data usage patterns
Give clear factual actionable IPDR-focused response."""
        else:
            system_context = f"""You are TeleForensic AI, expert AI investigation assistant for police telecom forensic analysis.

RULES:
- Respond in SAME LANGUAGE user types
- Telugu input → Telugu response
- Hindi → Hindi, Kannada → Kannada
- English → English
- Base answers only on provided data
- Always suggest investigation leads
- For non-investigation questions say: I am TeleForensic AI focused only on telecom forensic analysis

UPLOADED FILE DATA:
{file_context}

PATTERN ANALYSIS:
{findings_text}

SUSPICION SCORES:
{scores_text}

CHAT HISTORY:
{chat_history}

INVESTIGATOR QUESTION: {user_message}

Give clear factual actionable response."""
        
        # Generate response
        response = model.generate_content(system_context)
        return response.text
        
    except Exception as e:
        error_msg = f"Error getting AI response: {str(e)}"
        print(error_msg)
        return f"Sorry, I encountered an error: {error_msg}. Please check your API key and try again."

def format_history(messages):
    """Format chat history as readable string"""
    try:
        if not messages:
            return "No previous messages"
        
        history_parts = []
        for msg in messages[-10:]:  # Show last 10 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            history_parts.append(f"{role}: {content}")
        
        return "\n".join(history_parts)
        
    except Exception as e:
        print(f"Error formatting history: {e}")
        return "Error formatting chat history"

def detect_language(text):
    """Detect language of user input"""
    try:
        # Simple language detection based on characters
        telugu_chars = set('అఆఇఈఉఊఋఌఎఏఐఒఓఔకఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరఱలళవశషసహ')
        hindi_chars = set('अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह')
        kannada_chars = set('ಅಆಇಈಉಊಋಎಏಐಒಓಔಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಱಲಳವಶಷಸಹ')
        
        text_chars = set(text)
        
        if text_chars & telugu_chars:
            return 'telugu'
        elif text_chars & hindi_chars:
            return 'hindi'
        elif text_chars & kannada_chars:
            return 'kannada'
        else:
            return 'english'
            
    except Exception as e:
        print(f"Error detecting language: {e}")
        return 'english'

def is_investigation_query(text):
    """Check if query is related to investigation"""
    try:
        investigation_keywords = [
            'suspect', 'suspicious', 'pattern', 'analysis', 'investigation',
            'call', 'phone', 'number', 'tower', 'location', 'frequency',
            'suspic', 'risk', 'threat', 'criminal', 'evidence', 'proof',
            'అనుమానం', 'సందేశం', 'ఫోన్', 'కాల్', 'స్థానం', 'నిందితుడు',
            'संदिग्ध', 'जांच', 'फोन', 'कॉल', 'स्थान', 'आरोपी',
            'ಅನುಮಾನ', 'ತನಿಖೆ', 'ಫೋನ್', 'ಕಾಲ್', 'ಸ್ಥಳ', 'ಆರೋಪಿ'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in investigation_keywords)
        
    except Exception as e:
        print(f"Error checking investigation query: {e}")
        return True  # Default to investigation query

def validate_api_key(api_key):
    """Validate Gemini API key format"""
    try:
        if not api_key or len(api_key) < 20:
            return False
        
        # Basic validation - Gemini API keys are typically long alphanumeric strings
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False
        
        return True
        
    except Exception as e:
        print(f"Error validating API key: {e}")
        return False

def get_sample_questions():
    """Get sample investigation questions"""
    return [
        "Who are the high risk phone numbers?",
        "Show me suspicious calling patterns",
        "Which numbers make frequent night calls?",
        "Are there any sequential number series?",
        "Who has the most missed calls?",
        "What are the top suspicious patterns?",
        "Show me numbers with short call durations",
        "Which locations have high risk activity?"
    ]