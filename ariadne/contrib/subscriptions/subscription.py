from typing import AsyncGenerator


class Subscription:
    def __init__(self, operation_name: str, async_generator: AsyncGenerator):
        self.operation_name = operation_name
        self.async_generator = async_generator
