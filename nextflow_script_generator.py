# This class generates next flow modules.
# It's methods are called by the frontend written in NodeGraphQT.


### IN PROGRESS ###


import shutil   # For copying files
import os       # For creating file paths

def copy_template(template_file, tool_name, new_file_name):
    source_file = template_file
    destination_file = os.path.join(tool_name, new_file_name) # Create a directory with the new tool name and file name

    try:
        # Copy the file
        shutil.copy2(source_file, destination_file)
        print(f"File copied successfully from {source_file} to {destination_file}.")

    except shutil.SameFileError:
        print("Source and destination represent the same file.")
    except PermissionError:
        print("Permission denied.")
    except FileNotFoundError:
        print("The source or destination file was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        
    return destination_file

class ScriptGenerator:
    def __init__(self, parent=None):
        self.tool = ""
        self.tool_execution_path = ""
        self.input_file_type = ""
        self.input_file_path = ""
        self.output_file_path = ""
    
    def generate_single_tool_nf(self):
        """
        Template for nextflow module written in nextflow.
        """
        file = copy_template("templates/template.nf", "fastqc", "fastqc.nf")

        with open(file, w) as file:
            file.write("process " + self.tool +  "{")

if __name__ == '__main__':
    s = ScriptGenerator()

