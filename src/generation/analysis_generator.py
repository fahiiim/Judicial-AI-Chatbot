"""
Analysis generator for detailed case analysis and punishment recommendations
Provides comprehensive legal analysis with organized output
"""
import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class AnalysisGenerator:
    """Generate detailed legal analysis from retrieved documents"""
    
    def __init__(self):
        """Initialize the analysis generator"""
        self.punishment_keywords = [
            'fined', 'imprisoned', 'imprisonment', 'sentence', 'sentenced',
            'penalty', 'punished', 'years', 'fine', 'term of years',
            'life imprisonment', 'death', 'probation', 'restitution',
            'supervised release', 'confined'
        ]
        
        self.offense_keywords = [
            'offense', 'crime', 'felony', 'misdemeanor', 'violation',
            'unlawful', 'illegal', 'prohibited', 'shall not', 'whoever'
        ]
    
    def generate_analysis(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Generate comprehensive analysis from retrieved documents
        
        Args:
            query: Original user query
            retrieved_docs: List of retrieved legal documents
            
        Returns:
            Formatted analysis string with offense description and punishment
        """
        if not retrieved_docs:
            return self._format_no_documents_response()
        
        # Extract key information from documents
        offense_desc = self._extract_offense_description(retrieved_docs)
        punishment_info = self._extract_punishment_info(retrieved_docs)
        related_sections = self._extract_sections(retrieved_docs)
        key_elements = self._extract_key_elements(retrieved_docs)
        
        # Format as organized analysis
        analysis = self._format_analysis(
            query,
            offense_desc,
            punishment_info,
            related_sections,
            key_elements
        )
        
        return analysis
    
    def _extract_offense_description(self, docs: List[Dict[str, Any]]) -> str:
        """Extract offense description from documents"""
        descriptions = []
        
        for doc in docs:
            text = doc.get('text', '').lower()
            
            # Look for offense-related content
            if any(kw in text for kw in self.offense_keywords):
                # Extract relevant sentences
                sentences = re.split(r'[.!?]', doc.get('text', ''))
                for sentence in sentences:
                    if any(kw in sentence.lower() for kw in self.offense_keywords):
                        if len(sentence.strip()) > 20:
                            descriptions.append(sentence.strip())
        
        # Return top 3 descriptions
        return " ".join(descriptions[:3]) if descriptions else "Offense under federal law"
    
    def _extract_punishment_info(self, docs: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract punishment information from documents"""
        punishment = {
            'fine': None,
            'imprisonment': None,
            'other_penalties': []
        }
        
        for doc in docs:
            text = doc.get('text', '')
            
            # Look for fine amounts
            fine_match = re.search(r'fined.*?under this title', text, re.IGNORECASE)
            if fine_match and not punishment['fine']:
                punishment['fine'] = "Fine under applicable federal law"
            
            # Look for imprisonment terms
            term_matches = re.findall(
                r'imprisoned.*?(?:for|not|more than|any term of|life|years)',
                text, re.IGNORECASE
            )
            if term_matches and not punishment['imprisonment']:
                # Get the most specific term
                for term in term_matches:
                    if 'life' in term.lower() or 'death' in term.lower():
                        punishment['imprisonment'] = term.strip()
                        break
                    elif 'years' in term.lower():
                        punishment['imprisonment'] = term.strip()
                        break
            
            # Extract other penalties
            other_penalties = re.findall(
                r'(?:restitution|probation|supervised release|forfeit)',
                text, re.IGNORECASE
            )
            for penalty in other_penalties:
                if penalty not in punishment['other_penalties']:
                    punishment['other_penalties'].append(penalty)
        
        return punishment
    
    def _extract_sections(self, docs: List[Dict[str, Any]]) -> List[str]:
        """Extract section numbers from documents"""
        sections = []
        
        for doc in docs:
            # Look for section references like § or section numbers
            section_matches = re.findall(
                r'(?:§|section)\s*(\d+(?:\([a-z0-9)]*\))?)',
                doc.get('text', ''),
                re.IGNORECASE
            )
            sections.extend(section_matches)
        
        # Return unique sections
        return list(set(sections))[:5]  # Top 5 sections
    
    def _extract_key_elements(self, docs: List[Dict[str, Any]]) -> List[str]:
        """Extract key elements of the offense"""
        elements = []
        element_keywords = [
            'intentionally', 'knowingly', 'willfully', 'recklessly',
            'with intent', 'without consent', 'force', 'threat',
            'property', 'person', 'value', 'amount'
        ]
        
        for doc in docs:
            text = doc.get('text', '')
            for keyword in element_keywords:
                if keyword.lower() in text.lower():
                    # Extract surrounding context
                    idx = text.lower().find(keyword.lower())
                    start = max(0, idx - 30)
                    end = min(len(text), idx + 100)
                    context = text[start:end].strip()
                    
                    if context not in elements and len(context) > 20:
                        elements.append(context)
        
        return elements[:3]  # Top 3 key elements
    
    def _format_analysis(
        self,
        query: str,
        offense_desc: str,
        punishment: Dict[str, str],
        sections: List[str],
        key_elements: List[str]
    ) -> str:
        """Format analysis in organized, descriptive format"""
        
        analysis = []
        analysis.append("=" * 80)
        analysis.append("⚖️  LEGAL ANALYSIS & CASE ASSESSMENT")
        analysis.append("=" * 80)
        
        # 1. Case Overview
        analysis.append("\n📋 CASE OVERVIEW:")
        analysis.append("-" * 80)
        analysis.append(f"Query: {query}")
        analysis.append("")
        
        # 2. Offense Description
        analysis.append("📌 OFFENSE DESCRIPTION:")
        analysis.append("-" * 80)
        if offense_desc:
            analysis.append(self._clean_text(offense_desc[:500]))
        else:
            analysis.append("Federal criminal offense under 18 U.S.C.")
        analysis.append("")
        
        # 3. Key Elements
        if key_elements:
            analysis.append("🔍 KEY ELEMENTS OF THE OFFENSE:")
            analysis.append("-" * 80)
            for i, element in enumerate(key_elements, 1):
                cleaned = self._clean_text(element)
                analysis.append(f"{i}. {cleaned}")
            analysis.append("")
        
        # 4. Applicable Sections
        if sections:
            analysis.append("📜 APPLICABLE LEGAL SECTIONS:")
            analysis.append("-" * 80)
            for section in sections:
                analysis.append(f"  • 18 U.S.C. § {section}")
            analysis.append("")
        
        # 5. Punishment Assessment
        analysis.append("⚠️  PUNISHMENT & PENALTIES:")
        analysis.append("-" * 80)
        
        if punishment['imprisonment']:
            analysis.append(f"Imprisonment:")
            analysis.append(f"  {self._clean_text(punishment['imprisonment'])}")
        
        if punishment['fine']:
            analysis.append(f"\nFines:")
            analysis.append(f"  {punishment['fine']}")
        
        if punishment['other_penalties']:
            analysis.append(f"\nAdditional Penalties:")
            for penalty in punishment['other_penalties']:
                analysis.append(f"  • {penalty.title()}")
        
        analysis.append("")
        
        # 6. Summary
        analysis.append("💡 LEGAL SUMMARY:")
        analysis.append("-" * 80)
        summary = self._generate_summary(query, punishment, sections)
        analysis.append(summary)
        analysis.append("")
        
        # 7. Disclaimer
        analysis.append("⚠️  IMPORTANT DISCLAIMER:")
        analysis.append("-" * 80)
        analysis.append("This analysis is based on federal criminal law (18 U.S.C.) and should")
        analysis.append("NOT be considered legal advice. For legal guidance, consult a licensed")
        analysis.append("attorney in your jurisdiction. This chatbot provides informational")
        analysis.append("content only. Actual sentences depend on various factors including:")
        analysis.append("  • Prior criminal history")
        analysis.append("  • Severity of the offense")
        analysis.append("  • Aggravating/mitigating circumstances")
        analysis.append("  • Judge's discretion")
        analysis.append("  • Federal sentencing guidelines")
        analysis.append("=" * 80)
        
        return "\n".join(analysis)
    
    def _generate_summary(
        self,
        query: str,
        punishment: Dict[str, str],
        sections: List[str]
    ) -> str:
        """Generate a comprehensive, natural language summary with detailed legal judgment"""
        
        summary_parts = []
        
        # Opening statement with legal framework
        if sections:
            section_refs = ", ".join([f"18 U.S.C. § {s}" for s in sections[:3]])
            summary_parts.append(
                f"Under federal law, specifically {section_refs}, the conduct described in your query "
                f"constitutes a serious criminal offense under the United States Code. "
            )
        else:
            summary_parts.append(
                "Under applicable federal criminal law, the conduct described in your query "
                "constitutes a serious criminal offense that is prosecuted in federal courts. "
            )
        
        # Detailed legal analysis
        summary_parts.append(
            "This offense falls within the jurisdiction of federal authorities and is subject to "
            "prosecution under Title 18 of the United States Code, which defines a wide range of "
            "criminal conduct that affects interstate commerce, federal interests, and public safety. "
        )
        
        # Punishment assessment details
        summary_parts.append("\n\n")
        summary_parts.append("POTENTIAL CONSEQUENCES AND PUNISHMENTS:\n\n")
        
        if punishment['imprisonment']:
            summary_parts.append(
                f"Imprisonment: Individuals convicted of this offense face significant terms of "
                f"incarceration. The specific duration depends on the statutory penalties outlined in "
                f"the applicable statute. Federal sentences are typically determinate, meaning the "
                f"exact length is decided by the sentencing judge within the parameters established "
                f"by Congress and federal sentencing guidelines.\n\n"
            )
        else:
            summary_parts.append(
                "Imprisonment: Conviction of this federal offense carries substantial risk of "
                "incarceration, with sentence lengths determined by federal sentencing guidelines "
                "and the judge's discretionary authority within congressionally mandated ranges.\n\n"
            )
        
        if punishment['fine']:
            summary_parts.append(
                f"Financial Penalties: Beyond imprisonment, convicted individuals face substantial "
                f"monetary fines. Federal fines can reach hundreds of thousands of dollars or more, "
                f"depending on the nature and severity of the offense. These financial penalties serve "
                f"as both punishment and deterrent.\n\n"
            )
        
        if punishment['other_penalties']:
            penalties_list = ", ".join([p.lower() for p in punishment['other_penalties']])
            summary_parts.append(
                f"Additional Penalties: In addition to imprisonment and fines, courts may impose "
                f"supplementary sanctions including {penalties_list}. These measures are designed to "
                f"ensure victim restitution, protect public safety, and maintain judicial supervision "
                f"of the defendant after release from custody.\n\n"
            )
        
        # Mitigating and aggravating factors
        summary_parts.append(
            "FACTORS AFFECTING SENTENCING:\n\n"
            "Federal judges do not operate under a fixed sentencing framework but rather within "
            "guidelines and statutory ranges. The following factors significantly influence the "
            "severity of punishment:\n\n"
            "• Criminal History: Defendants with prior convictions typically receive enhanced sentences. "
            "The extent of prior criminal conduct is quantified and directly impacts sentencing ranges.\n\n"
            "• Nature and Severity: The specific circumstances of the offense—including violence involved, "
            "property damage, number of victims, and premeditation—substantially increase penalties.\n\n"
            "• Defendant's Role: Whether the accused was a principal actor, accomplice, or minor participant "
            "affects culpability and sentencing. Leadership roles typically result in harsher penalties.\n\n"
            "• Aggravating Circumstances: Factors such as use of weapons, targeting vulnerable victims, "
            "commission of the offense while on release, or involvement of multiple offenses increase sentences.\n\n"
            "• Mitigating Circumstances: Acceptance of responsibility, cooperation with authorities, "
            "mental health issues, family hardship, and lack of prior criminal history may reduce sentences.\n\n"
            "• Federal Sentencing Guidelines: While not mandatory, these guidelines provide recommended "
            "ranges that judges typically follow, creating some predictability in sentencing outcomes.\n\n"
        )
        
        # Procedural context
        summary_parts.append(
            "LEGAL PROCEDURES AND ENFORCEMENT:\n\n"
            "Federal prosecutions follow rigorous procedures designed to protect defendants' constitutional "
            "rights while ensuring public safety. Investigation by federal law enforcement agencies precedes "
            "any charging decision. Prosecution occurs in federal district courts with strict rules of evidence "
            "and procedure. The defendant has the right to legal representation, the presumption of innocence, "
            "and the right to trial by jury. Conviction requires proof beyond a reasonable doubt on all elements "
            "of the offense.\n\n"
        )
        
        # Closing judgment
        summary_parts.append(
            "OVERALL ASSESSMENT:\n\n"
            "The conduct described in your query, if substantiated through evidence, would likely result in "
            "federal criminal prosecution with serious consequences. Given the federal nature of the offense and "
            "the enforcement resources of the federal government, prosecution would proceed through federal courts "
            "in the appropriate jurisdiction. The resulting conviction would carry life-altering consequences including "
            "significant imprisonment, substantial fines, loss of civil rights, and permanent impact on employment, "
            "housing, and social standing. Every case is unique, and actual outcomes depend heavily on the specific facts, "
            "applicable law, quality of legal representation, and prosecutorial discretion."
        )
        
        return "".join(summary_parts)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for display"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters
        text = re.sub(r'[""'']', '"', text)
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text.strip()
    
    def _format_no_documents_response(self) -> str:
        """Format response when no documents are found"""
        return (
            "=" * 80 + "\n"
            "⚖️  LEGAL ANALYSIS\n"
            "=" * 80 + "\n\n"
            "No specific legal information found in the database for your query.\n"
            "This may indicate that the offense you're asking about is not covered\n"
            "in the 18 U.S.C. (Federal Criminal Law) database.\n\n"
            "For accurate legal information, please:\n"
            "  • Consult with a licensed attorney\n"
            "  • Check your state or local laws (if applicable)\n"
            "  • Review the full U.S. Code at www.justice.gov\n\n"
            "=" * 80
        )
