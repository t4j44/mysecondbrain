"""Canonical enum vocabularies, mirrored from supabase/migrations.

These are the ONLY values PostgreSQL accepts. PGEnum needs them: without values
SQLAlchemy cannot map an enum column on the way back out of the database.
Regenerate whenever a migration adds or removes an enum value.
"""

ENUM_VALUES: dict[str, tuple[str, ...]] = {
    "ai_message_role": ("system", "user", "assistant", "tool", "function"),
    "ai_message_status": ("pending", "streaming", "completed", "error"),
    "content_status": ("draft", "review", "published", "archived", "scheduled"),
    "document_processing_status": ("pending", "processing", "completed", "failed"),
    "export_job_status": ("queued", "processing", "completed", "failed", "expired"),
    "export_job_type": ("markdown", "json", "full_archive", "backup", "portfolio"),
    "idea_status": ("captured", "draft", "exploring", "validating", "prioritized", "building", "executing", "paused", "rejected", "completed", "archived"),
    "integration_provider": ("google_drive", "google_calendar", "gmail", "github", "linkedin", "custom"),
    "integration_status": ("connected", "disconnected", "syncing", "error", "revoked"),
    "interaction_type": ("meeting", "call", "email", "chat", "event", "note", "social_touch", "work_session"),
    "kpi_category": ("founder", "network", "learning", "venture", "personal"),
    "kpi_period": ("daily", "weekly", "monthly", "quarterly", "yearly"),
    "meeting_status": ("scheduled", "in_progress", "completed", "cancelled", "rescheduled"),
    "project_status": ("planned", "active", "blocked", "paused", "completed", "archived", "on_hold"),
    "relationship_type": ("mentor", "investor", "peer", "collaborator", "lead", "contact", "customer", "advisor", "team"),
    "sync_job_status": ("pending", "running", "completed", "failed", "retrying"),
    "sync_job_type": ("calendar_sync", "drive_backup", "contacts_sync", "export", "incremental_backup"),
    "task_priority": ("low", "medium", "high", "urgent"),
    "task_status": ("backlog", "todo", "in_progress", "blocked", "completed", "cancelled", "archived", "done"),
    "venture_status": ("active", "paused", "completed", "archived", "exited"),
    "visibility_status": ("private", "shared", "public", "unlisted"),
}
