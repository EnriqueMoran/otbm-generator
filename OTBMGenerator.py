from lib import json2otbm
from lib import otbm2json


__author__ = "EnriqueMoran"

__version__ = "v0.1.1"


class OTBMGenerator:
    """
    Open Tibia Bit Map and respawn files generator.
    """

    def __init__(self):
        self.otbm2json_parser = otbm2json.Otbm2Json()
        self.json2otbm_parser = json2otbm.Json2Otbm()