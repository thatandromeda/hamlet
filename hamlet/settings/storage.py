from whitenoise.storage import CompressedStaticFilesStorage

class WhiteNoiseStaticFilesStorage(CompressedStaticFilesStorage):
    manifest_strict = False
