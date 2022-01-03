import os
import sys
import time

sys.path.append(os.path.join(sys.path[0], '..'))    # noqa: E402

import OTBMGenerator


def main(example):
    otbm_file = None    # Input file
    json_file = None    # Output file
    if example == 1:
        otbm_file = "./otbmparser_files/example1.otbm"
        json_file = "./output/example1_output.json"
    elif example == 2:
        otbm_file = "./otbmparser_files/example2.otbm"
        json_file = "./output/example2_output.json"
    elif example == 3:
        otbm_file = "./otbmparser_files/example3.otbm"
        json_file = "./output/example3_output.json"
    else:
        print("Please provide a valid example value (1, 2 3).")
        return

    start_time = time.process_time()    # Time measurement

    # Create OTBMGenerator instance and set input & output files path
    otbm_generator = OTBMGenerator.OTBMGenerator()
    otbm_generator.otbm2json_parser.otbm_file_path = otbm_file
    otbm_generator.otbm2json_parser.json_file_path = json_file

    # Process OTBM file, parsing its data to json
    otb2json.process_file()

    # Save generated json with map data.
    otb2json.generate_json()

    elapsed = time.process_time() - start_time
    path = os.path.abspath(json_file)
    print(f"Parsing finished in {elapsed} seconds!, saved in {path}")

if __name__ == "__main__":
    main(example=1)    # Valid values: 1, 2, 3
