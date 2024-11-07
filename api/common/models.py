from django.db import models

class AutoCreatedUpdatedMixin(models.Model):
    """Mixin to add auto-managed creation and update timestamps."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Automatically set when instance is created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="Automatically updated on each save."
    )

    class Meta:
        abstract = True