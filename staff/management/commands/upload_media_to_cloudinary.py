from pathlib import Path

import cloudinary
import cloudinary.uploader
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Upload local media files directly to Cloudinary with media/ prefix.'

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
            secure=True,
        )

        if not media_root.exists():
            self.stdout.write(self.style.ERROR(f'MEDIA_ROOT not found: {media_root}'))
            return

        files = [p for p in media_root.rglob('*') if p.is_file()]
        uploaded = 0
        failed = 0

        self.stdout.write(f'Found files: {len(files)}')

        for index, file_path in enumerate(files, start=1):
            relative_path = file_path.relative_to(media_root).as_posix()
            public_id = f"media/{Path(relative_path).with_suffix('').as_posix()}"

            self.stdout.write(f'[{index}/{len(files)}] UPLOADING {relative_path} -> {public_id}')

            try:
                cloudinary.uploader.upload(
                    str(file_path),
                    public_id=public_id,
                    overwrite=True,
                    resource_type='image',
                )
                uploaded += 1
                self.stdout.write(self.style.SUCCESS(f'OK {public_id}'))
            except Exception as error:
                failed += 1
                self.stdout.write(self.style.ERROR(f'FAIL {relative_path}: {error}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Uploaded: {uploaded}. Failed: {failed}.'))
