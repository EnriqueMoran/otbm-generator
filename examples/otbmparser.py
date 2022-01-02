import os
import sys

sys.path.append(os.path.join(sys.path[0], '..'))


from lib import otbmparser


def main(example):
    otbm_file = None
    output_file = None
    if example == 1:
        otbm_file = "./otbmparser_files/example1.otbm"
        output_file = "./output/example1_output.json"
    elif example == 2:
        otbm_file = "./otbmparser_files/example2.otbm"
        output_file = "./output/example2_output.json"
    elif example == 3:
        otbm_file = "./otbmparser_files/example3.otbm"
        output_file = "./output/example3_output.json"
    else:
        print("Please provide a valid example value (1, 2 3).")
        return

    otb2json = otbmparser.OTBMParser()
    otb2json.file_path = otbm_file
    otb2json.process_file()
    otb2json.generate_json(output_file)  

if __name__ == "__main__":
    main(example=1)    # Valid values: 1, 2, 3