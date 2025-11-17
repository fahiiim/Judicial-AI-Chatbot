"""
Conversation Manager for attorney-like legal consultation flow
Manages multi-turn conversations with greeting, detail gathering, consent, and analysis
"""
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage attorney-like legal consultation conversation flow"""
    
    def __init__(self):
        """Initialize conversation manager"""
        self.conversation_history = []
        self.case_details = {
            "initial_issue": "",
            "additional_context": [],
            "dates": [],
            "parties_involved": [],
            "damages_or_harm": "",
            "prior_incidents": "",
            "evidence": []
        }
        self.conversation_state = "greeting"  # States: greeting -> gathering -> consent -> analysis
        self.user_ready_for_analysis = False
        
    def get_greeting(self) -> str:
        """Return attorney-like greeting"""
        return (
            "="*80 + "\n"
            "⚖️  FEDERAL CRIMINAL LAW CONSULTATION\n"
            "="*80 + "\n\n"
            "Good day. I'm your legal consultation assistant, specialized in federal criminal law\n"
            "under Title 18 of the United States Code.\n\n"
            "I'm here to help you understand the legal implications of your situation and provide\n"
            "comprehensive analysis based on applicable federal statutes.\n\n"
            "To provide you with accurate and thorough legal assessment, I'll need to gather some\n"
            "details about your situation. This conversation will be professional, confidential,\n"
            "and focused on helping you understand the relevant legal framework.\n\n"
            "Let's begin. Could you please describe the main issue or situation you'd like to\n"
            "discuss? Please provide as much context as you feel comfortable sharing.\n"
            "="*80 + "\n"
        )
    
    def process_initial_issue(self, user_input: str) -> Tuple[str, bool]:
        """Process initial issue description and ask follow-up questions
        
        Args:
            user_input: User's initial issue description
            
        Returns:
            Tuple of (response_text, should_continue_gathering)
        """
        self.case_details["initial_issue"] = user_input
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        # Generate follow-up questions based on the issue
        response = (
            "\n" + "-"*80 + "\n"
            "Thank you for providing that information. I have a good understanding of the\n"
            "initial issue. To conduct a thorough analysis, I need to gather additional details.\n\n"
            "Let me ask you some clarifying questions:\n\n"
            "1. TIMELINE: When did this incident occur? (Please provide specific dates or\n"
            "   approximate timeframe - e.g., last week, 3 months ago, etc.)\n"
            "   \n"
            "   Type your response:\n"
        )
        
        return response, True
    
    def process_timeline(self, user_input: str) -> Tuple[str, bool]:
        """Process timeline information and ask next question"""
        self.case_details["dates"].append(user_input)
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        response = (
            "\n" + "-"*80 + "\n"
            "Thank you for that information. Understanding the timeline is crucial for\n"
            "legal analysis.\n\n"
            "2. PARTIES INVOLVED: Who are the parties involved in this situation?\n"
            "   (e.g., yourself, other individuals, organizations, government agencies, etc.)\n"
            "   Please describe their roles and relationships.\n"
            "   \n"
            "   Type your response:\n"
        )
        
        return response, True
    
    def process_parties(self, user_input: str) -> Tuple[str, bool]:
        """Process parties information"""
        self.case_details["parties_involved"].append(user_input)
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        response = (
            "\n" + "-"*80 + "\n"
            "I understand the parties involved. This is important context.\n\n"
            "3. HARM OR DAMAGE: What was the nature and extent of any harm, damage, or loss?\n"
            "   (e.g., physical injury, property damage, financial loss, etc.)\n"
            "   Please be as specific as possible about the impact.\n"
            "   \n"
            "   Type your response:\n"
        )
        
        return response, True
    
    def process_harm(self, user_input: str) -> Tuple[str, bool]:
        """Process harm/damage information"""
        self.case_details["damages_or_harm"] = user_input
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        response = (
            "\n" + "-"*80 + "\n"
            "Thank you for that important detail. The nature and extent of harm significantly\n"
            "impacts legal analysis and potential penalties.\n\n"
            "4. PRIOR INCIDENTS: Are there any prior incidents, complaints, or related matters?\n"
            "   (e.g., previous conflicts, reported issues, ongoing disputes, etc.)\n"
            "   Or type 'none' if there are no prior incidents.\n"
            "   \n"
            "   Type your response:\n"
        )
        
        return response, True
    
    def process_prior_incidents(self, user_input: str) -> Tuple[str, bool]:
        """Process prior incidents information"""
        self.case_details["prior_incidents"] = user_input
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        response = (
            "\n" + "-"*80 + "\n"
            "I see. Prior incidents or patterns can be important for legal analysis.\n\n"
            "5. EVIDENCE: What evidence or documentation do you have regarding this situation?\n"
            "   (e.g., communications, witnesses, medical records, photographs, receipts, etc.)\n"
            "   Or type 'none' if you don't have documentation.\n"
            "   \n"
            "   Type your response:\n"
        )
        
        return response, True
    
    def process_evidence(self, user_input: str) -> Tuple[str, bool]:
        """Process evidence information and prepare for consent"""
        self.case_details["evidence"].append(user_input)
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        # Now ask for consent before providing analysis
        response = (
            "\n" + "="*80 + "\n"
            "CASE INFORMATION SUMMARY\n"
            "="*80 + "\n\n"
            "Thank you for providing these comprehensive details. I now have a clear understanding\n"
            "of your situation:\n\n"
            f"• Initial Issue: {self.case_details['initial_issue'][:100]}...\n"
            f"• Timeline: {self.case_details['dates'][0][:50]}...\n"
            f"• Parties Involved: {self.case_details['parties_involved'][0][:50]}...\n"
            f"• Harm/Damage: {self.case_details['damages_or_harm'][:50]}...\n\n"
            "="*80 + "\n\n"
            "READY FOR LEGAL ANALYSIS\n\n"
            "I am now prepared to provide you with a comprehensive legal analysis and case\n"
            "assessment based on applicable federal criminal law (Title 18, U.S. Code).\n\n"
            "This analysis will include:\n"
            "  • Description of the applicable offense(s)\n"
            "  • Key elements required for criminal liability\n"
            "  • Relevant federal statutes and regulations\n"
            "  • Potential penalties and consequences\n"
            "  • Factors affecting sentencing\n"
            "  • Overall legal assessment\n\n"
            "Before I proceed with the detailed legal analysis, I need your confirmation:\n\n"
            "Should I provide you with the complete LEGAL ANALYSIS & CASE ASSESSMENT now?\n"
            "Or is there additional context or details you'd like to share first?\n\n"
            "Please respond with:\n"
            "  • 'yes' or 'proceed' - To receive the legal analysis now\n"
            "  • 'more' or 'additional' - If you have more details to share\n"
            "  • 'change' - If you'd like to modify something from your previous responses\n\n"
            "="*80 + "\n"
        )
        
        self.conversation_state = "consent"
        return response, True
    
    def process_consent(self, user_input: str) -> Tuple[str, bool]:
        """Process user consent for legal analysis
        
        Returns:
            Tuple of (response, should_provide_analysis)
        """
        user_input_lower = user_input.lower().strip()
        
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "user",
            "message": user_input
        })
        
        if user_input_lower in ['yes', 'proceed', 'ok', 'okay', 'y']:
            self.user_ready_for_analysis = True
            self.conversation_state = "analysis"
            
            response = (
                "\n" + "="*80 + "\n"
                "GENERATING COMPREHENSIVE LEGAL ANALYSIS\n"
                "="*80 + "\n\n"
                "Based on your detailed case information, I am now analyzing applicable federal\n"
                "statutes, case law precedents, and sentencing guidelines to provide you with a\n"
                "thorough legal assessment.\n\n"
                "Please review the following analysis carefully:\n\n"
            )
            
            return response, True  # Signal to proceed with analysis
        
        elif user_input_lower in ['more', 'additional', 'yes more', 'more details']:
            response = (
                "\n" + "-"*80 + "\n"
                "Understood. Please provide the additional context or details you'd like to share.\n"
                "This information will help me provide more accurate legal analysis.\n\n"
                "Type your additional information:\n"
            )
            
            return response, False  # Don't provide analysis yet
        
        elif user_input_lower in ['change', 'modify', 'back', 'previous']:
            response = (
                "\n" + "-"*80 + "\n"
                "I understand you'd like to modify some information. You can provide the\n"
                "corrected details now, or we can restart the consultation.\n\n"
                "What would you like to change or clarify?\n"
            )
            
            return response, False  # Don't provide analysis yet
        
        else:
            response = (
                "\n" + "-"*80 + "\n"
                "I didn't quite understand your response. Please clarify:\n\n"
                "Do you want me to:\n"
                "  • 'yes' - Proceed with the legal analysis now\n"
                "  • 'more' - Provide additional details first\n"
                "  • 'change' - Modify any previous information\n\n"
            )
            
            return response, False
    
    def get_case_summary(self) -> str:
        """Return formatted case summary"""
        summary = (
            "\n" + "="*80 + "\n"
            "CASE DETAILS SUMMARY\n"
            "="*80 + "\n\n"
            f"INITIAL ISSUE:\n{self.case_details['initial_issue']}\n\n"
            f"TIMELINE:\n{self.case_details['dates'][0] if self.case_details['dates'] else 'Not specified'}\n\n"
            f"PARTIES INVOLVED:\n{self.case_details['parties_involved'][0] if self.case_details['parties_involved'] else 'Not specified'}\n\n"
            f"HARM/DAMAGE:\n{self.case_details['damages_or_harm']}\n\n"
            f"PRIOR INCIDENTS:\n{self.case_details['prior_incidents']}\n\n"
            f"EVIDENCE:\n{self.case_details['evidence'][0] if self.case_details['evidence'] else 'None'}\n\n"
            "="*80 + "\n"
        )
        
        return summary
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Return conversation history"""
        return self.conversation_history
    
    def reset_conversation(self):
        """Reset conversation for new case"""
        self.conversation_history = []
        self.case_details = {
            "initial_issue": "",
            "additional_context": [],
            "dates": [],
            "parties_involved": [],
            "damages_or_harm": "",
            "prior_incidents": "",
            "evidence": []
        }
        self.conversation_state = "greeting"
        self.user_ready_for_analysis = False
