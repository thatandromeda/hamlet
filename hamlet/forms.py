from captcha.fields import CaptchaField

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


# By analogy with django.core.validators.FileExtensionValidator source.
@deconstructible
class MimetypeValidator:
    message = "The MIME type is not valid (it appears to be '%(mimetype)s'). Allowed MIME types are: '%(allowed_mimetypes)s'."  # noqa

    def __init__(self, allowed_mimetypes=None):
        if allowed_mimetypes is not None:
            allowed_mimetypes = [allowed_mimetype.lower() for allowed_mimetype in allowed_mimetypes]  # noqa
        self.allowed_mimetypes = allowed_mimetypes

    def __call__(self, value):
        if value.content_type not in self.allowed_mimetypes:
            raise ValidationError(self.message %
                {'mimetype': value.content_type,
                 'allowed_mimetypes': ', '.join(self.allowed_mimetypes)})


@deconstructible
class FileSizeValidator:
    message = 'The file is too large (%(size)s KB). The maximum file size is %(allowed_size)s KB.'  # noqa

    def __init__(self, max_size=2 * 1024 * 1024):
        self.max_size = max_size

    def __call__(self, value):
        if len(value) >= self.max_size:
            raise ValidationError(self.message %
                {'size': round(len(value) / 1024),
                 'allowed_size': round(self.max_size / 1024)})


class UploadFileForm(forms.Form):
    allowed_extensions = ['txt', 'docx']
    allowed_mimetypes = ['text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']  # noqa
    max_size = 4 * 1024 * 1024

    file = forms.FileField(
        validators=[FileSizeValidator(max_size),
                    FileExtensionValidator(allowed_extensions),
                    MimetypeValidator(allowed_mimetypes)],
        widget=forms.ClearableFileInput(attrs={'class': 'field field-upload'}),
        help_text='.txt or .docx only.')
    captcha = CaptchaField(help_text='Sorry, no spammers.')
