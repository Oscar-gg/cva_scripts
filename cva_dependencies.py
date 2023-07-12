class ViewDependencies:

  def __init__ (self, directory_path, direct_dependencies, project_extensions):
    self.directory_path = os.path.abspath(directory_path)
    self.direct_dependencies = direct_dependencies
    self.project_extensions = project_extensions

    self.set_initial_variables()


  def set_initial_variables(self):
    self.project_checked_files = set()
    self.project_file_dependencies = set()
    extensions_available = ViewDependencies.all_file_extensions(self.directory_path)
    self.search_pattern = ViewDependencies.get_pattern(extensions_available)


  def process_direct_dependencies(self):
    for dependency in self.direct_dependencies:
      path_to_dependency = os.path.join(self.directory_path, dependency)
      
      path_to_dependency = os.path.abspath(path_to_dependency)

      if os.path.isdir(path_to_dependency):
        self.get_directory_dependencies(path_to_dependency) 
      elif os.path.isfile(path_to_dependency) and ViewDependencies.get_file_extension(path_to_dependency) in self.project_extensions:
        self.process_file_dependencies(path_to_dependency)
      else:
        print("Warning: DIRECT dependency does not exist: " + path_to_dependency)


  def get_directory_dependencies(self, path_to_directory):
    for root, _, files in os.walk(path_to_directory):
      for file in files:
        file_path = os.path.join(root, file)
        if os.path.isfile(file_path):
          self.project_file_dependencies.add(file_path)
          if ViewDependencies.get_file_extension(file_path) in self.project_extensions:
            self.process_file_dependencies(file_path)
        else:
          print("Warning: directory dependency does not exist: " + file_path)
        

  def process_file_dependencies(self, path_to_file):
    if path_to_file in self.project_checked_files:
      return

    self.project_checked_files.add(path_to_file)

    file_dependencies_list = self.general_file_dependencies(path_to_file)

    for file_path in file_dependencies_list:
      if os.path.isfile(file_path):
          self.project_file_dependencies.add(file_path)
          if ViewDependencies.get_file_extension(file_path) in self.project_extensions:
            self.process_file_dependencies(file_path)
      else:
        print(f"Warning: file dependency does not exist: {file_path}")
        print(f"File was referenced in {path_to_file}")


  def general_file_dependencies(self, path_to_file):
    ext = ViewDependencies.get_file_extension(path_to_file)
    if ext in [".js"]:
      return self.get_javascript_file_dependencies(path_to_file, self.search_pattern)
    elif ext in self.project_extensions:
      return self.get_file_dependencies(path_to_file, self.search_pattern)
    else:
      print(f"Warning: extension {ext} is not included. {path_to_file}")


  def get_file_dependencies(self, path_to_file, search_pattern):
    file_list = []
    file_as_string = ViewDependencies.read_file_as_string(path_to_file)

    matches = re.findall(search_pattern, file_as_string)
    dirname = os.path.dirname(path_to_file)

    for match in matches:
      dependency = match[1]

      discard, dependency_path = self.possible_paths(path_to_file, dependency)
      if discard:
        continue

      file_list.append(dependency_path)
    
    return file_list


  def get_javascript_file_dependencies(self, path_to_file, general_search_pattern):
    file_list = []

    # Para imports especificos de javascript
    js_pattern = r"""import(\s*([^;<>]+)\s*from\s*|\s+)(["'])([^"\']+)(\3);"""

    file_as_string = ViewDependencies.read_file_as_string(path_to_file)
    matches_javascript = re.findall(js_pattern, file_as_string)
    dirname = os.path.dirname(path_to_file)

    for match in matches_javascript:
      file_name = match[3]
      # Ignorar file si no tiene directorio, añadir file si tiene algún directorio.
      if not os.path.dirname(file_name) == "":
        dependency_name = os.path.join(dirname, file_name)
        file_list.append(dependency_name)
    
    # Procesar otros tipos de paths usando patrón genérico
    # Si el path tiene algun directorio en común con el archivo, asumir que está
    # en ese directorio. 
    matches = re.findall(general_search_pattern, file_as_string)

    for match in matches:
      dependency = match[1]

      # Saltar archivos sin folder en arhivos .js
      if os.path.dirname(dependency) == "":
        continue
      
      discard, dependency_path = self.possible_paths(path_to_file, dependency)
      if discard:
        continue

      file_list.append(dependency_path)
    
    return file_list


  def possible_paths(self, path_to_file, dependency_path_in_file):
    """If path is not found, try to search the original path within the path_to_file. If it isn't found, try to search it in the directory_path."""
    dirname = os.path.dirname(path_to_file)

    dependency_path = os.path.join(dirname, dependency_path_in_file)
    dependency_path = os.path.normpath(dependency_path)
    if os.path.isfile(dependency_path):
      return [False, dependency_path]

    dependency_path = ViewDependencies.merge_paths(path_to_file, dependency_path_in_file)
    discard = False

    # If merged path wasn't found, try attaching the path to the original directory.
    if not os.path.isfile(dependency_path):
      discard, dependency_path = self.discard_path(dirname, dependency_path_in_file)
    
    if os.path.isfile(dependency_path) and False:
      print(f"Info: Found dependency: {dependency_path}.")
    return [discard, dependency_path]


  def discard_path(self, dirname, file_name):
    # Discard path only if it starts with http, to handle matched http links.
    if file_name.startswith("http"):
      return [True, ""]

    actual_path = os.path.normpath(os.path.join(dirname, file_name))

    # If path can't be found, try to find it in the directory_path
    if not os.path.isfile(actual_path):
      actual_path = os.path.join(self.directory_path, file_name)
      actual_path = os.path.normpath(actual_path)
      actual_path = os.path.abspath(actual_path)

    return [False, actual_path]


  def merge_paths(parent_path, child_path):
    """Returns location of child_path inside parent_path, assuming child_path is contained within parent_path."""
    parent_folders = ViewDependencies.folders_in_path(parent_path)
    dir_child = os.path.dirname(child_path)
    base_name = os.path.basename(child_path)

    for folder in parent_folders:
      if folder.endswith(dir_child):
        return os.path.join(folder, base_name)

    if False:
        print(f"Info: failed to find {child_path} within {parent_path}.")
    return "Failed"


  def folders_in_path(path):
    folders = []

    while len(path) > 1:
      folders.append(os.path.dirname(path))
      path = os.path.dirname(path);

    list.reverse(folders)
    return folders 


  def show_unused_files(self):
    print("Unused files:")
    for root, _, files in os.walk(self.directory_path):
      for file in files:
        file_path = os.path.join(root, file)
        
        if file_path not in self.project_file_dependencies:
          print(file_path)  
  

  def show_unused_directories(self):
    print("Unused directories:")
    for root, dirs, _ in os.walk(self.directory_path):
      for directory in dirs:
        directory_path = os.path.join(root, directory)

        if self.dir_is_unused(directory_path):
          print(directory_path)
        

  def dir_is_unused(self, directory):
    for root, _, files in os.walk(directory):
      for file in files:
        file_path = os.path.join(root, file)
        if file_path in self.project_file_dependencies:
            return False
    
    return True


  def get_file_extension(path_to_file):
    _, ext = os.path.splitext(path_to_file)
    return ext
  

  def all_file_extensions(directory_path):
    file_types = set()
    for root, _, files in os.walk(directory_path):
      for file in files:
        file_path = os.path.join(root, file)
        file_types.add(ViewDependencies.get_file_extension(file_path))

    return list(file_types)


  def get_pattern(ext):
    pattern_end = '('

    for i in range(len(ext)):
      if ext[i] == "":
        continue

      pattern_end += ext[i][1:] # Quitar . de la extension

      if i != len(ext) - 1:
        pattern_end += "|"

    pattern_end += ')'
    pattern = r"""(['"])(([^'<>"]*)\.""" + pattern_end + r"\s*)(\1)"
    return pattern


  def read_file_as_string(file_path, encoding='latin-1'):
    with open(file_path, 'r', encoding=encoding) as file:
      file_contents = file.read()
      return ViewDependencies.clean_string(file_contents)


  # Remove line breaks
  def clean_string(file_as_string):
    return file_as_string.replace('\n', '')
  