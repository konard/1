"""
Future AI module for content analysis and generation.

This module will be used for:
- Comment sentiment analysis
- Content idea generation
- Video script generation
- Automated publishing (requires OAuth)

Current implementation uses stub classes that return placeholder data.
"""

from .interfaces import (
    CommentAnalyzer,
    ContentIdeaGenerator,
    ScriptGenerator,
    AutoPublisher,
    StubCommentAnalyzer,
    StubContentIdeaGenerator,
    StubScriptGenerator,
    StubAutoPublisher,
)

__all__ = [
    "CommentAnalyzer",
    "ContentIdeaGenerator",
    "ScriptGenerator",
    "AutoPublisher",
    "StubCommentAnalyzer",
    "StubContentIdeaGenerator",
    "StubScriptGenerator",
    "StubAutoPublisher",
]
