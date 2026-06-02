"""
rules/urls.py
────────────────────────────────────────────────────────────────────────────────
Rule routes are split across two prefixes in api/urls.py:
  /api/v1/datasets/<dataset_id>/rules/  → RuleListCreateView
  /api/v1/rules/<id>/                   → RuleDetailView
"""

from django.urls import path

from .views import RuleDetailView, RuleListCreateView

urlpatterns = [
    # Nested under datasets — list and create
    path(
        "datasets/<uuid:dataset_id>/rules/",
        RuleListCreateView.as_view(),
        name="rule-list-create",
    ),
    # Standalone — retrieve, update, delete
    path(
        "rules/<uuid:rule_id>/",
        RuleDetailView.as_view(),
        name="rule-detail",
    ),
]
