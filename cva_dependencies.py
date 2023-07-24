# @Oscar-gg

class ViewDependencies:

  def __init__ (self, directory_path, direct_dependencies, project_extensions, log_level = 2):
    self.directory_path = os.path.abspath(directory_path)
    self.direct_dependencies = direct_dependencies
    self.project_extensions = project_extensions
    self.log_level = log_level


  def process_direct_dependencies(self):
    self.set_initial_variables()

    for dependency in self.direct_dependencies:
      path_to_dependency = os.path.join(self.directory_path, dependency)

      path_to_dependency = os.path.abspath(path_to_dependency)

      if os.path.isdir(path_to_dependency):
        self.get_directory_dependencies(path_to_dependency)
      elif os.path.isfile(path_to_dependency) and ViewDependencies.get_file_extension(path_to_dependency) in self.project_extensions:
        self.process_file_dependencies(path_to_dependency)
      else:
        self.log_message(2, f"DIRECT dependency does not exist: {path_to_dependency}")

  def set_initial_variables(self):
    self.project_checked_files = set()
    self.project_file_dependencies = set()
    extensions_available = ViewDependencies.all_file_extensions(self.directory_path)
    self.search_pattern = ViewDependencies.get_pattern(extensions_available)
    self.project_size = ViewDependencies.directory_size(self.directory_path)

  def show_unused_files(self, threshold_kb=0, exclude_extensions=[]):
    unused_files = []
    for root, _, files in os.walk(self.directory_path):
      for file in files:
        file_path = os.path.join(root, file)

        if file_path not in self.project_file_dependencies:
          unused_files.append(file_path)

    sort_files = []
    total_size = 0
    for file in unused_files:
      size_kb = ViewDependencies.file_size_kb(file)
      total_size += size_kb
      sort_files.append((size_kb, file))

    sort_files.sort(reverse=True)

    unused_size_str = ViewDependencies.size_to_string(total_size)
    project_size_str = ViewDependencies.size_to_string(self.project_size)
    threshold_size_str = ViewDependencies.size_to_string(threshold_kb)
    print(f"Size of unused files: {unused_size_str} (out of {project_size_str})")
    print(f"Showing list of unused files above {threshold_size_str}:")

    for file in sort_files:
      if file[0] < threshold_kb:
        break

      if ViewDependencies.get_file_extension(file[1]) in exclude_extensions:
        continue

      size_str = ViewDependencies.size_to_string(file[0])
      print(f"{size_str}: {file[1]}")


  def show_unused_directories(self):
    print("Unused directories:")
    directories = []
    for root, dirs, _ in os.walk(self.directory_path):
      for directory in dirs:
        directory_path = os.path.join(root, directory)

        if self.dir_is_unused(directory_path):
          directories.append(directory_path)

    directories = ViewDependencies.remove_contained_directories(directories)

    # Sort directories by size and display.
    sorted_dirs = []
    for directory in directories:
      sorted_dirs.append((ViewDependencies.directory_size(directory), directory))

    sorted_dirs.sort(reverse=True)

    for directory in sorted_dirs:
      directory_size_str = ViewDependencies.size_to_string(directory[0])
      print(f"{directory_size_str}: {directory[1]}")


  def show_used_files_in_directory(self, directory_path):
    path_to_dependency = os.path.join(self.directory_path, directory_path)
    path_to_dependency = os.path.abspath(path_to_dependency)
    path_to_dependency = os.path.normpath(path_to_dependency)

    if not os.path.isdir(path_to_dependency):
      self.log_message(1, f"Directory path doesn't exist: {path_to_dependency}")
      return

    used_files = self.dir_used_files(path_to_dependency)

    if (len(used_files) == 0):
      print(f"The directory {path_to_dependency} doesn't contain dependency files.")
    else:
      print(f"Used files in {path_to_dependency}:")
      for file in used_files:
        print(file)

  def show_unused_files_in_directory(self, directory_path):
    path_to_dependency = os.path.join(self.directory_path, directory_path)
    path_to_dependency = os.path.abspath(path_to_dependency)
    path_to_dependency = os.path.normpath(path_to_dependency)

    if not os.path.isdir(path_to_dependency):
      self.log_message(1, f"Directory path doesn't exist: {path_to_dependency}")
      return

    unused_files = self.dir_unused_files(path_to_dependency)

    if (len(unused_files) == 0):
      print(f"The directory {path_to_dependency} doesn't contain unused files.")
    else:
      print(f"Unused files in {path_to_dependency}:")
      for file in unused_files:
        print(file)

  def get_directory_dependencies(self, path_to_directory):
    for root, _, files in os.walk(path_to_directory):
      for file in files:
        file_path = os.path.join(root, file)
        if os.path.isfile(file_path):
          self.project_file_dependencies.add(file_path)
          if ViewDependencies.get_file_extension(file_path) in self.project_extensions:
            self.process_file_dependencies(file_path)
        else:
          self.log_message(2, f"directory dependency does not exist: {file_path}")


  def process_file_dependencies(self, path_to_file):
    if path_to_file in self.project_checked_files:
      return

    self.project_checked_files.add(path_to_file)
    self.project_file_dependencies.add(path_to_file)

    file_dependencies_list = self.general_file_dependencies(path_to_file)

    for file_path in file_dependencies_list:
      if os.path.isfile(file_path):
          self.project_file_dependencies.add(file_path)
          if ViewDependencies.get_file_extension(file_path) in self.project_extensions:
            self.process_file_dependencies(file_path)
      else:
        self.log_message(2, f"file dependency does not exist: {file_path}.\nFile was referenced in {path_to_file}")


  def general_file_dependencies(self, path_to_file):
    ext = ViewDependencies.get_file_extension(path_to_file)
    file_dependencies = []
    if ext in [".js"]:
      file_dependencies = self.get_javascript_file_dependencies(path_to_file, self.search_pattern)
    elif ext in self.project_extensions:
      file_dependencies = self.get_file_dependencies(path_to_file, self.search_pattern)
    else:
      self.log_message(2, f"Extension {ext} is not included: {path_to_file}")

    for i in range(len(file_dependencies)):
      file_dependencies[i] = os.path.normpath(file_dependencies[i])

    return file_dependencies


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
    js_pattern = r"""import(\s*([^;<>]+)\s*from\s*|\s+)(["'])([^"\';]+)(\3);?"""

    file_as_string = ViewDependencies.read_file_as_string(path_to_file)
    matches_javascript = re.findall(js_pattern, file_as_string)
    dirname = os.path.dirname(path_to_file)

    for match in matches_javascript:
      file_name = match[3]
      # Ignorar file si no tiene directorio, añadir file si tiene algún directorio.
      if not os.path.dirname(file_name) == "":
        file_name += ".js"
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

    dependency_path = self.merge_paths(path_to_file, dependency_path_in_file)
    discard = False

    # If merged path wasn't found, try attaching the path to the original directory.
    if not os.path.isfile(dependency_path):
      discard, dependency_path = self.discard_path(dirname, dependency_path_in_file)

    if os.path.isfile(dependency_path):
      self.log_message(3, f"Found dependency: {dependency_path}.")
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


  def merge_paths(self, parent_path, child_path):
    """Returns location of child_path inside parent_path, assuming child_path is contained within parent_path."""
    parent_folders = ViewDependencies.folders_in_path(parent_path)
    dir_child = os.path.dirname(child_path)
    base_name = os.path.basename(child_path)

    for folder in parent_folders:
      if folder.endswith(dir_child):
        return os.path.join(folder, base_name)

    self.log_message(3, f"failed to find {child_path} within {parent_path}.")

    return "Failed"


  def folders_in_path(path):
    folders = []
    past = os.path.dirname(path)

    while len(path) > 1 and path != past:
      folders.append(os.path.dirname(path))
      past = path
      path = os.path.dirname(path)

    list.reverse(folders)
    return folders


  def remove_contained_directories(directory_list):
    directories = []
    for i in range(len(directory_list)):
      contained = False
      for j in range(len(directory_list)):
        if i!=j and directory_list[i].startswith(directory_list[j]):
          contained = True
          break

      if not contained:
        directories.append(directory_list[i])

    return directories


  def directory_size(directory_path):
    total_size = 0
    for root, _, files in os.walk(directory_path):
      for file in files:
        file_path = os.path.join(root, file)
        total_size += ViewDependencies.file_size_kb(file_path)

    return total_size


  def file_size_kb(file_path):
    return os.path.getsize(file_path) / 1024


  def dir_is_unused(self, directory):
    for root, _, files in os.walk(directory):
      for file in files:
        file_path = os.path.join(root, file)
        if file_path in self.project_file_dependencies:
            return False

    return True


  def dir_used_files(self, directory):
    used_dir_files = []
    for root, _, files in os.walk(directory):
      for file in files:
        file_path = os.path.join(root, file)
        if file_path in self.project_file_dependencies:
            used_dir_files.append(file_path)

    return used_dir_files

  def dir_unused_files(self, directory):
    unused_dir_files = []
    for root, _, files in os.walk(directory):
      for file in files:
        file_path = os.path.join(root, file)
        if file_path not in self.project_file_dependencies:
            unused_dir_files.append(file_path)

    return unused_dir_files


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


  def read_file_as_string(file_path, encoding_='utf-8'):
    with open(file_path, 'r', encoding=encoding_) as file:
      file_contents = file.read()
      return ViewDependencies.clean_string(file_contents)


  # Remove line breaks
  def clean_string(file_as_string):
    return file_as_string.replace('\n', '')


  def log_message(self, log_level, message):

    if log_level > self.log_level:
      return

    tag = ""

    if log_level == 1:
      tag = "Error: "
    elif log_level == 2:
      tag = "Warning: "
    elif log_level == 3:
      tag = "Info: "

    print(f"{tag}{message}")


  def size_to_string(size_in_kb):

    sizes = ["kb", "mb", "gb", "tb"]
    new_size = size_in_kb
    counter = 0

    while new_size > 1024 and counter < len(sizes):
      new_size = new_size / 1024
      counter += 1

    return f"{new_size:.2f} {sizes[counter]}"