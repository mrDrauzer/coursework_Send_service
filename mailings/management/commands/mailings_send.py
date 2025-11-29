from django.core.management.base import BaseCommand
from django.utils import timezone

from mailings.models import Mailing
from mailings.services import is_within_window, run_mailing


class Command(BaseCommand):
    help = "Отправить рассылки, которые находятся в окне времени (start/end)."

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, help='ID конкретной рассылки (опционально)')

    def handle(self, *args, **options):
        mailing_id = options.get('id')

        qs = Mailing.objects.all()
        if mailing_id:
            qs = qs.filter(pk=mailing_id)
        else:
            # Только не завершённые
            qs = qs.exclude(status=Mailing.Status.FINISHED)

        total = 0
        processed = 0
        for mailing in qs:
            total += 1
            # Защита от повторного запуска завершённой рассылки даже при передаче --id
            if mailing.status == Mailing.Status.FINISHED:
                self.stdout.write(self.style.NOTICE(
                    f"Skip mailing #{mailing.pk}: already FINISHED"
                ))
                continue
            if not is_within_window(mailing):
                continue
            # Пометить как RUNNING и выполнить
            mailing.status = Mailing.Status.RUNNING
            mailing.save(update_fields=['status'])
            ok, err = run_mailing(mailing)
            processed += 1
            self.stdout.write(self.style.SUCCESS(
                f"Mailing #{mailing.pk}: sent={ok}, errors={err}"
            ))

        self.stdout.write(self.style.NOTICE(
            f"Checked: {total}; processed: {processed} at {timezone.now():%Y-%m-%d %H:%M:%S}"
        ))
