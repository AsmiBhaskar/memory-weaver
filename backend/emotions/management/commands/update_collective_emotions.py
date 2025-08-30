from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from emotions.models import CollectiveEmotion, EmotionSession
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Background task to update collective emotions periodically'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Update interval in seconds'
        )
        parser.add_argument(
            '--max-runs',
            type=int,
            default=0,  # 0 = infinite
            help='Maximum number of runs (0 for infinite)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        max_runs = options['max_runs']
        run_count = 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting collective emotion updater (interval: {interval}s)')
        )
        
        try:
            while True:
                run_count += 1
                
                # Update collective emotions
                try:
                    collective = CollectiveEmotion()
                    collective.calculate_collective_emotions()
                    
                    self.stdout.write(
                        f'Updated collective emotions - Run {run_count} '
                        f'(Active sessions: {collective.active_sessions})'
                    )
                    
                except Exception as e:
                    logger.error(f'Error updating collective emotions: {e}')
                    self.stdout.write(
                        self.style.ERROR(f'Error in run {run_count}: {e}')
                    )
                
                # Clean up old inactive sessions
                try:
                    cutoff = timezone.now() - timedelta(hours=24)
                    old_sessions = EmotionSession.objects.filter(
                        is_active=True,
                        last_activity__lt=cutoff
                    )
                    
                    if old_sessions.exists():
                        count = old_sessions.count()
                        old_sessions.update(is_active=False)
                        self.stdout.write(f'Deactivated {count} old sessions')
                        
                except Exception as e:
                    logger.error(f'Error cleaning up sessions: {e}')
                
                # Check if we should stop
                if max_runs > 0 and run_count >= max_runs:
                    self.stdout.write(
                        self.style.SUCCESS(f'Completed {run_count} runs, stopping.')
                    )
                    break
                
                # Wait for next interval
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING(f'Stopped after {run_count} runs.')
            )
