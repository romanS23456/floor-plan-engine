"""Validation issues for Floor Plan Engine.

Structured ValidationIssue format for all validation, review, and operations.
"""

from typing import Dict, Any, Optional, List
from app.issue_taxonomy import get_issue_definition, get_default_severity, get_issue_category


def make_issue(
    code: str,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    entity_refs: Optional[List[Dict[str, str]]] = None,
    message: Optional[str] = None,
    consequence: Optional[str] = None,
    confidence: str = "medium",
    fixability: Optional[str] = None,
    source: str = "validation",
) -> Dict[str, Any]:
    """Create a structured ValidationIssue dict.
    
    Uses issue taxonomy defaults when parameters are not provided.
    Returns a plain JSON-serializable dict.
    """
    # Get taxonomy definition for defaults
    definition = get_issue_definition(code)
    
    # Use provided values or taxonomy defaults
    final_category = category if category else definition.get("category", "unknown")
    final_severity = severity if severity else definition.get("default_severity", "warning")
    final_message = message if message else definition.get("default_message", f"Issue: {code}")
    final_consequence = consequence if consequence else definition.get("default_consequence")
    final_confidence = confidence if confidence != "medium" else definition.get("default_confidence", "medium")
    final_fixability = fixability if fixability else definition.get("default_fixability", "unknown")
    
    # Generate stable ID
    if entity_refs:
        ids = "_".join([ref.get("id", "unknown") for ref in entity_refs])
        issue_id = f"issue_{code.lower()}_{ids}"
    else:
        issue_id = f"issue_{code.lower()}"
    
    # Build issue dict
    issue = {
        "id": issue_id,
        "code": code,
        "severity": final_severity,
        "category": final_category,
        "entity_refs": entity_refs if entity_refs else [],
        "message": final_message,
        "consequence": final_consequence,
        "confidence": final_confidence,
        "fixability": final_fixability,
        "source": source,
    }
    
    return issue
