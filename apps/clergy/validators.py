from django.core.exceptions import ValidationError

MAX_ATTESTATION_DOCUMENT_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_ATTESTATION_DOCUMENT_EXTENSIONS = ("pdf", "jpg", "jpeg", "png")


def validate_attestation_document_size(value):
    if value.size > MAX_ATTESTATION_DOCUMENT_SIZE_BYTES:
        raise ValidationError(
            f"File too large ({value.size / (1024 * 1024):.1f} MB). Maximum size is "
            f"{MAX_ATTESTATION_DOCUMENT_SIZE_BYTES // (1024 * 1024)} MB."
        )
