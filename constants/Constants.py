import os

class Constants():
    LOCAL_DATA_PATH = "/Users/haotian/Documents/documents-local/hercules/local_data"

    IS_PROD = os.environ.get("IS_PROD", False) == "True"

    USE_GCS = True 

    USE_CUDA = os.environ.get("USE_CUDA", False) == "True"

    GCS_BUCKET_NAME = "harmono_files_prod"

    GCS_DOWNLOADED_MUSICXMLS_BUCKET_NAME = "downloaded_musicxmls"

    API_BASE_URL = "http://localhost:8000/"

    GCP_PROJECT_ID = "harmono-prod"

    BACKGROUND_PUBSUB_TOPIC = "harmono_background_jobs" if IS_PROD else "harmono_background_jobs_test"

    BACKGROUND_PUBSUB_SUBSCRIPTION = "harmono_background_jobs-sub" if IS_PROD else "harmono_background_jobs_test-sub"

    #MONGO_URI = f"mongodb+srv://{os.environ['MONGO_USERNAME']}:{os.environ['MONGO_PASSWORD']}@harmono-test-deployment.nvxgkmc.mongodb.net/"
    MONGO_URI = f"mongodb+srv://{os.environ['MONGO_USERNAME']}:{os.environ['MONGO_PASSWORD']}@harmono-prod-deployment.ala3kpv.mongodb.net/"

    DB_NAME = "harmono_db"

    REDIS_HOST = "localhost"

    REDIS_PORT = 6379   # TODO remove

    REDIS_JOBS_LIST = "jobs"    # TODO remove

    PERF_COMPARISON_JOB = "perfcomparisonjob"

    PERF_PROCESSING_JOB = "perfprocessingjob"

    TMP_DIR = "/tmp"

    DEFAULT_MAX_PERFMID_SIZE = "600"


    # key: tuple of (min, max), value: actual value presented to LLM
    DYNAMICS_TREND_RATIO_MAP = {
        (-100, -0.5): -0.75,
        (-0.5, 0): -0.25,
        (0, 0.5): 0.25,
        (0.5, 100): 1 # LLM will praise
    }

    CORR_RIGHT_MAP = {
        (-1.0, 0): -0.5,
        (0, 0.5): 0.25,
        (0.5, 1.0): 0.75    # LLM will praise
    }

    SUS_PEDAL_EVENT_RATIO_MAP = {
        (0, 0.75): 0.75,
        (0.75, 1.25): 1,
        (1.25, 100): 1.5 
    }

    ONSET_TIME_TREND_RATIO_MAP = {
        (0, 0.9): 0.75,
        (0.9, 1.1): 1,
        (1.1, 100): 1.25,
    }

    MUSICAL_DIRECTION_RANGE = ["crescendo", "diminuendo"]


