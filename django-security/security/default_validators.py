from .throttling import PerRequestThrottlingValidator


validators = (
    PerRequestThrottlingValidator(3600, 1000),  # 1000 per an hour
    PerRequestThrottlingValidator(60, 20),  # 20 per an minute
)
