class HtmlText:
    def __init__(self, directory, files_to_process, prefix="Text_"):
        self.directory = directory
        self.files_to_process = files_to_process
        self.prefix = prefix


    def generate_text_files(self):
        for file in self.files_to_process:
            file_path = os.path.join(self.directory, file)
            file_path = os.path.abspath(file_path)
            
            if os.path.isfile(file_path):
                self.process_file(file_path)
            elif os.path.isdir(file_path):
                self.process_dir(file_path)
            else:
                print(f"File does not exist: {file_path}")


    def process_dir(self, dir_path):
        if not os.path.isdir(dir_path):
            print(f"Directory does not exist: {dir_path}")
            return

        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and HtmlText.get_file_extension(file_path) == ".html":
                    self.process_file(file_path)


    def process_file(self, file_path):
        if not os.path.isfile(file_path) or HtmlText.get_file_extension(file_path) != ".html":
            print(f"Invalid file path or file extension: {file_path}")
            return

        output_file_path = HtmlText.insert_prefix(self.prefix, file_path)
        output_file_path = HtmlText.change_extension(output_file_path, "txt")

        if os.path.isfile(output_file_path):
            print(f"File already exists: {output_file_path}")
            return
        
        text = HtmlText.get_text(file_path)
        if text is not None:
            HtmlText.write_text_file(output_file_path, text)


    def write_text_file(output_path, text):
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)


    def get_text(file_path):
        html_text = HtmlText.extract_text_from_local_html(file_path)
        if html_text is not None:
            return HtmlText.remove_consecutive_linebreaks(html_text)
        return None

    def extract_text_from_local_html(file_path):
        try:
            # Read the content from the local HTML file
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            # Extract all text from the parsed HTML
            all_text = soup.get_text()
            return all_text.strip()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except Exception as e:
            print(f"Error occurred while processing the HTML: {e}")
            return None

    def remove_consecutive_linebreaks(input_string):
        output_string = re.sub(r'\n+', '\n', input_string)
        return output_string

    def remove_generated_files(self):
        for root, _, files in os.walk(self.directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and HtmlText.get_file_extension(file_path) == ".txt" and file.startswith(self.prefix):
                    HtmlText.remove_file(file_path)

    def remove_file(file_path):
        try:
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        except Exception as e:
            print(f"Error occurred while deleting file: {file_path}")
            print(e)

    def get_file_extension(path_to_file):
        _, ext = os.path.splitext(path_to_file)
        return ext

    def insert_prefix(prefix, path_to_file):
        directory = os.path.dirname(path_to_file)
        filename = prefix + os.path.basename(path_to_file)
        return os.path.join(directory, filename)

    def change_extension(filename, new_extension):
        base_name, _ = os.path.splitext(filename)
        new_filename = base_name + "." + new_extension
        return new_filename