#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_philosophers_api import SourcePhilosophersApi

if __name__ == "__main__":
    source = SourcePhilosophersApi()
    launch(source, sys.argv[1:])
