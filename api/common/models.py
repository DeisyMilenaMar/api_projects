from django.db import models

class AutoCreatedUpdatedMixin(models.Model):
    """
    Mixin to add automatically managed creation and update timestamp fields
    to any models that inherit from this class. Inherits from models.Model
    for full ORM integration.
    """
    id = models.BigAutoField(
        primary_key=True,
        help_text="Unique ID for each model instance, generated automatically."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when this instance was created. Set automatically on creation."
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        help_text="Timestamp when this instance was last updated. Automatically updated on each save."
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = "Entry with auto timestamps"
        verbose_name_plural = "Entries with auto timestamps"
