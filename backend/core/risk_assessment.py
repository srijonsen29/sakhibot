"""
Risk Assessment Agent for Women Safety
Analyzes conversation to determine danger level and recommend actions.
"""

from datetime import datetime
from typing import Dict, List, Tuple
import re


class RiskAssessmentAgent:
    """
    Agent 5: Real-time risk assessment based on conversation analysis.
    Predicts danger level and triggers appropriate safety responses.
    """
    
    def __init__(self):
        # Risk indicators with severity weights (0-10 scale)
        self.risk_indicators = self._initialize_indicators()
    
    def _initialize_indicators(self) -> Dict:
        """Initialize risk indicators with keyword patterns."""
        return {
            'immediate_danger': {
                'keywords': [
                    'killing me', 'will kill', 'has weapon', 'has knife', 
                    'has gun', 'choking', 'cannot breathe', 'help now',
                    'maar dalega', 'jaan se maar', 'chaku hai', 'gun hai'
                ],
                'weight': 10,
                'action': 'immediate_intervention'
            },
            'physical_violence': {
                'keywords': [
                    'hitting', 'beating', 'slapping', 'punching', 'kicked',
                    'pushed', 'hurt', 'injured', 'bleeding', 'bruises',
                    'maar raha', 'peet raha', 'laat maar', 'thappad'
                ],
                'weight': 8,
                'action': 'urgent_safety_plan'
            },
            'threats': {
                'keywords': [
                    'threatened', 'warning', 'will hurt', 'will harm',
                    'or else', 'consequence', 'kill you', 'hurt children',
                    'dhamki', 'maarunga', 'dekh lunga', 'anjam'
                ],
                'weight': 7,
                'action': 'safety_planning'
            },
            'escalation': {
                'keywords': [
                    'getting worse', 'more frequent', 'everyday', 'again',
                    'started hitting', 'now he', 'this time', 'never before',
                    'pehle nahi', 'ab roz', 'badh gaya', 'zyada'
                ],
                'weight': 6,
                'action': 'document_pattern'
            },
            'isolation': {
                'keywords': [
                    'no family', 'cut off', 'alone', 'no friends',
                    'not allowed out', 'locked', 'phone taken',
                    'akeli', 'koi nahi', 'baat nahi', 'phone le liya'
                ],
                'weight': 6,
                'action': 'build_support'
            },
            'financial_control': {
                'keywords': [
                    'no money', 'bank account', 'no access', 'controls money',
                    'salary taken', 'cant buy', 'financial abuse',
                    'paise nahi', 'salary le leta', 'kharch nahi'
                ],
                'weight': 5,
                'action': 'economic_support'
            },
            'children_at_risk': {
                'keywords': [
                    'children scared', 'kids crying', 'hurt child',
                    'threatens kids', 'front of children', 'child witness',
                    'bachche dar', 'bachche ro', 'bachche dekh'
                ],
                'weight': 9,
                'action': 'child_protection'
            },
            'substance_abuse': {
                'keywords': [
                    'drunk', 'alcohol', 'drugs', 'intoxicated', 'high',
                    'comes home drunk', 'after drinking', 'when drunk',
                    'sharabi', 'nashe mein', 'daaru peke', 'nasha'
                ],
                'weight': 7,
                'action': 'unpredictable_danger'
            },
            'sexual_violence': {
                'keywords': [
                    'forced', 'against will', 'marital rape', 'sexual abuse',
                    'inappropriate', 'touched', 'molested',
                    'zabardasti', 'sexual violence', 'marital rape'
                ],
                'weight': 9,
                'action': 'immediate_legal'
            },
            'weapons_present': {
                'keywords': [
                    'knife', 'gun', 'weapon', 'blade', 'pistol',
                    'threatened with', 'showed weapon',
                    'chaku', 'bandook', 'hathiyar'
                ],
                'weight': 10,
                'action': 'immediate_intervention'
            }
        }
    
    def assess_risk(self, conversation_history: List[Dict], 
                   user_context: Dict = None) -> Dict:
        """
        Analyze full conversation to assess risk level.
        
        Args:
            conversation_history: List of messages with role and content
            user_context: Additional context (location, past incidents, etc.)
        
        Returns:
            Risk assessment with level, score, and recommended actions
        """
        risk_scores = {key: 0 for key in self.risk_indicators.keys()}
        matched_indicators = []
        
        # Analyze each message
        for msg in conversation_history:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                
                for category, data in self.risk_indicators.items():
                    for keyword in data['keywords']:
                        if keyword in content:
                            risk_scores[category] = data['weight']
                            matched_indicators.append({
                                'category': category,
                                'keyword': keyword,
                                'message': content[:100]
                            })
                            break  # Count each category once per message
        
        # Calculate total risk
        total_risk = sum(risk_scores.values())
        max_possible = sum(data['weight'] for data in self.risk_indicators.values())
        risk_percentage = (total_risk / max_possible) * 100
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_percentage, risk_scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, risk_scores, matched_indicators
        )
        
        return {
            'risk_level': risk_level['level'],
            'risk_score': total_risk,
            'risk_percentage': round(risk_percentage, 1),
            'severity': risk_level['severity'],
            'categories_detected': [k for k, v in risk_scores.items() if v > 0],
            'matched_indicators': matched_indicators,
            'recommendations': recommendations,
            'immediate_action_required': risk_level['level'] in ['critical', 'severe'],
            'timestamp': datetime.now().isoformat(),
            'alert_authorities': risk_level['level'] == 'critical'
        }
    
    def _determine_risk_level(self, risk_percentage: float, 
                             risk_scores: Dict) -> Dict:
        """Determine risk level based on score and critical indicators."""
        
        # Check for critical indicators
        critical_categories = ['immediate_danger', 'weapons_present', 
                              'children_at_risk', 'sexual_violence']
        has_critical = any(risk_scores.get(cat, 0) > 0 for cat in critical_categories)
        
        if has_critical or risk_percentage >= 70:
            return {
                'level': 'critical',
                'severity': 'IMMEDIATE DANGER',
                'color': 'red',
                'priority': 1
            }
        elif risk_percentage >= 50:
            return {
                'level': 'severe',
                'severity': 'HIGH RISK',
                'color': 'orange',
                'priority': 2
            }
        elif risk_percentage >= 30:
            return {
                'level': 'high',
                'severity': 'ELEVATED RISK',
                'color': 'yellow',
                'priority': 3
            }
        elif risk_percentage >= 15:
            return {
                'level': 'moderate',
                'severity': 'MODERATE CONCERN',
                'color': 'blue',
                'priority': 4
            }
        else:
            return {
                'level': 'low',
                'severity': 'GENERAL INQUIRY',
                'color': 'green',
                'priority': 5
            }
    
    def _generate_recommendations(self, risk_level: Dict, 
                                 risk_scores: Dict,
                                 matched_indicators: List) -> Dict:
        """Generate actionable recommendations based on risk."""
        
        recommendations = {
            'immediate_actions': [],
            'safety_steps': [],
            'legal_steps': [],
            'support_resources': [],
            'documentation': []
        }
        
        level = risk_level['level']
        
        if level == 'critical':
            recommendations['immediate_actions'] = [
                '🚨 CALL 181 (Women\'s Helpline) RIGHT NOW',
                '🚨 Call 100 (Police Emergency) immediately',
                '📍 Share your live location with trusted contact',
                '🏃 Leave to a safe location if possible',
                '🏥 Seek medical attention if injured',
                '📱 Keep phone charged and accessible'
            ]
            recommendations['safety_steps'] = [
                'Do NOT return home alone',
                'Go to nearest police station or One Stop Centre',
                'Inform a trusted neighbor or friend immediately',
                'If locked in, try to reach a window or door'
            ]
        
        elif level == 'severe':
            recommendations['immediate_actions'] = [
                '📞 Call 181 Women\'s Helpline for guidance',
                '📍 Share your location with a trusted person',
                '👜 Prepare an emergency bag (see safety steps)',
                '📱 Keep important contacts saved'
            ]
            recommendations['safety_steps'] = [
                'Identify safe places you can go quickly',
                'Pack emergency bag: ID, money, phone charger, clothes, medicines',
                'Memorize important phone numbers',
                'Plan escape route from home',
                'Inform trusted neighbor about situation'
            ]
        
        elif level == 'high':
            recommendations['safety_steps'] = [
                'Create a safety plan with escape routes',
                'Keep emergency bag ready',
                'Document all incidents with dates and details',
                'Take photos of injuries (if any)',
                'Identify 2-3 safe places to go'
            ]
            recommendations['legal_steps'] = [
                'Consult with DLSA for free legal aid',
                'Know your rights under DV Act 2005',
                'Consider filing FIR if physical violence',
                'Apply for protection order under DV Act Section 18'
            ]
        
        else:
            recommendations['safety_steps'] = [
                'Document concerning behaviors and incidents',
                'Build support network of friends/family',
                'Know your legal rights',
                'Identify resources in your area'
            ]
        
        # Add specific recommendations based on detected categories
        if risk_scores.get('children_at_risk', 0) > 0:
            recommendations['immediate_actions'].insert(0,
                '👶 PROTECT CHILDREN - remove them from situation if possible'
            )
            recommendations['legal_steps'].append(
                'File for child custody under DV Act Section 21'
            )
        
        if risk_scores.get('financial_control', 0) > 0:
            recommendations['legal_steps'].append(
                'Apply for monetary relief under DV Act Section 20'
            )
            recommendations['support_resources'].append(
                'Open separate bank account if possible'
            )
        
        if risk_scores.get('sexual_violence', 0) > 0:
            recommendations['legal_steps'].insert(0,
                'File FIR under IPC Section 376 (rape) - includes marital rape'
            )
            recommendations['immediate_actions'].insert(0,
                '🏥 Get medical examination done immediately (evidence)'
            )
        
        # Documentation advice (always important)
        recommendations['documentation'] = [
            'Maintain diary with dates, times, incidents',
            'Save threatening messages/emails',
            'Take photos of injuries',
            'Keep medical reports safe',
            'Record witness names and contact info',
            'Store evidence in secure cloud storage'
        ]
        
        # Support resources (always included)
        recommendations['support_resources'] = [
            '181 - Women\'s Helpline (24x7)',
            '1091 - Women in Distress (Police)',
            '7827-170-170 - NCW Helpline',
            'Nearest One Stop Centre (24x7 support)',
            'DLSA for free legal aid',
            'iCall 9152987821 - Psychosocial support'
        ]
        
        return recommendations
    
    def check_immediate_danger(self, message: str) -> Tuple[bool, str]:
        """
        Quick check for immediate danger keywords.
        Used for real-time alerts during chat.
        
        Returns:
            (is_immediate_danger, matched_keyword)
        """
        message_lower = message.lower()
        
        immediate_keywords = (
            self.risk_indicators['immediate_danger']['keywords'] +
            self.risk_indicators['weapons_present']['keywords']
        )
        
        for keyword in immediate_keywords:
            if keyword in message_lower:
                return True, keyword
        
        return False, None
    
    def generate_safety_alert(self, risk_assessment: Dict) -> Dict:
        """
        Generate formatted safety alert for display.
        """
        level = risk_assessment['risk_level']
        
        if level == 'critical':
            return {
                'title': '🚨 IMMEDIATE DANGER DETECTED',
                'message': (
                    'Your safety is at risk. Please take immediate action.\n\n'
                    'CALL 181 RIGHT NOW or press the SOS button below.'
                ),
                'color': 'red',
                'show_sos_button': True,
                'auto_alert_guardians': True,
                'priority': 'critical'
            }
        
        elif level == 'severe':
            return {
                'title': '⚠️ HIGH RISK SITUATION',
                'message': (
                    'Your situation appears dangerous. Please consider:\n'
                    '• Calling 181 Women\'s Helpline\n'
                    '• Creating a safety plan\n'
                    '• Informing a trusted contact'
                ),
                'color': 'orange',
                'show_sos_button': True,
                'auto_alert_guardians': False,
                'priority': 'high'
            }
        
        else:
            return {
                'title': 'Safety Resources Available',
                'message': 'I\'m here to help. Let me know if you need immediate assistance.',
                'color': 'blue',
                'show_sos_button': False,
                'auto_alert_guardians': False,
                'priority': 'normal'
            }


def run(message: str, history: List[Dict] = None) -> Dict:
    """
    Main entry point for risk assessment.
    Can be called from orchestrator as Agent 5.
    """
    agent = RiskAssessmentAgent()
    
    if history is None:
        history = [{'role': 'user', 'content': message}]
    
    # Perform risk assessment
    assessment = agent.assess_risk(history)
    
    # Check for immediate danger
    is_immediate, keyword = agent.check_immediate_danger(message)
    
    if is_immediate:
        assessment['immediate_danger_detected'] = True
        assessment['danger_keyword'] = keyword
    
    # Generate safety alert
    alert = agent.generate_safety_alert(assessment)
    
    return {
        'risk_assessment': assessment,
        'safety_alert': alert,
        'immediate_danger': is_immediate,
        'recommendations': assessment['recommendations'],
        'trigger_sos': assessment['risk_level'] == 'critical'
    }
