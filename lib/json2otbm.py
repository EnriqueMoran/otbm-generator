import ijson
import os
import traceback

from pathlib import Path


class Json2Otbm:
    """
    Json to OTBM parser.
    """
    NODE_INIT = b'\xfe'
    NODE_END = b'\xff'
    NODE_SKIP = b'\xfd'

    def __init__(self):
        self._file_path = None

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        new_path = Path(value)
        assert new_path.is_file(), "File not found!"
        assert new_path.suffix == ".json", "Wrong file format!"
        self._file_path = new_path

    def _get_json_header(self, iterator):
        pass

    def process_file(self):
        with open(self.file_path, 'rb') as file:
            for k, v in ijson.kvitems(file, 'MAP'):
                print(k, v)

    def generate_otbm(self, output_file):
        """
        Create output otbm file with json data.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w+', encoding='utf-8') as f:
            pass

def main():
    parser = Json2Otbm()
    parser.file_path = "../examples/output/example1_output.json"
    output_file = "../output_otbm.otbm"
    parser.process_file()
    parser.generate_otbm(output_file)


if __name__ == "__main__":
    main()