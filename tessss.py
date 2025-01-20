import os
import json
import argparse
from json_repair import repair_json

def minimize_json_structure(json_data):
    """
    Extracts the bare-bone structure of a JSON object, representing lists
    by the structure of their first element.
    """
    if isinstance(json_data, dict):
        return {k: minimize_json_structure(v) for k, v in json_data.items()}
    elif isinstance(json_data, list):
        if json_data:
            return [minimize_json_structure(json_data[0])]
        else:
            return []
    else:
        return json_data  # Keep primitive values as they are

def process_json_files(directory):
    """
    Processes all JSON files in the given directory, minimizes their structures,
    repairs the JSON if necessary, and saves the results to the current directory.
    """
    current_directory = os.getcwd()

    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r') as f:
                    json_string = f.read()
                    try:
                        json_data = json.loads(json_string)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON in {filename} before minimization: {e}")
                        continue  # Skip to the next file if initial load fails

                    minimized_structure = minimize_json_structure(json_data)

                    output_filename = f"minimized_{filename}"
                    output_filepath = os.path.join(current_directory, output_filename)

                    # Attempt to dump the minimized structure directly
                    try:
                        with open(output_filepath, 'w') as outfile:
                            json.dump(minimized_structure, outfile, indent=4)
                        print(f"Minimized structure for {filename} saved to {output_filename}")
                    except json.JSONDecodeError:
                        # If dumping fails, attempt to repair the JSON string
                        minimized_json_string = json.dumps(minimized_structure)
                        repaired_json_string = repair_json(minimized_json_string)
                        try:
                            repaired_data = json.loads(repaired_json_string)
                            with open(output_filepath, 'w') as outfile:
                                json.dump(repaired_data, outfile, indent=4)
                            print(f"Minimized and repaired structure for {filename} saved to {output_filename}")
                        except json.JSONDecodeError as e:
                            print(f"Error repairing and saving JSON for {filename}: {e}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process JSON files in a directory, minimize their structures, and save the results to the current directory with JSON repair.")
    parser.add_argument("directory", help="The directory containing the JSON files.")
    args = parser.parse_args()

    directory_path = args.directory

    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a valid directory.")
    else:
        process_json_files(directory_path)