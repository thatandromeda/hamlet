from django.core.management.base import BaseCommand

from hamlet.neural.train_neural_net import ModelTrainer


class Command(BaseCommand):
    help = 'Run the neural net machinery'

    def add_arguments(self, parser):
        parser.add_argument('filename', help="Base filename of saved model")
        parser.add_argument('-d', '--dryrun',
                            help="dry run (don't train neural net)",
                            action='store_true')
        parser.add_argument('-w', '--write-metadata',
                            help="Write metadata to db",
                            action='store_true')

    def handle(self, *args, **options):
        mt = ModelTrainer()
        mt.execute(options)
        self.stdout.write(self.style.SUCCESS('Done'))
