# By @Oscar-gg

# Class to perform image reduction / compressing to reduce file size,
# taking into account image type and options
# Supports: .png, .jpg, .jpeg, .gif

class ImageReduction:

  def __init__(self, threshold_kb = 500, min_quality=60, colors_png=128,
               extensions=[".png", ".jpg",".jpeg", ".gif"],
               max_img_width_px=1000, max_img_height_px=1000, resize=False, reduce_all_valid_files=False,
               output_reduce_prefix="IR_", output_resize_prefix = "R_", best_prefix="B_", max_resize=0.6,
               colors_=32, scale_ratio='0.5', lossiness_factor='80'):

    self.threshold_kb = threshold_kb # Reducir solo imágenes que tengan peso mayor

    # La menor calidad a intentar (se usan calidades mayores primero), para jpg
    self.min_quality = min_quality

    self.colors_png = colors_png # Cantidad de colores a usar en png, potencia de 2.

    # Solo hay implementación para .png y .jpg. Si se agregan más solo apareceran
    # en print_files_above_threshold(). Quitar .png o .jpg para ignorar archivos
    self.extensions = extensions

    # Si es verdadero, al reducir una imagen se hace resize().
    self.resize = resize

    # Si es verdadero, va a intentar reducir todas las imágenes,
    # incluso las que estén por debajo del threshold.
    # Muy poco recomendable ponerlo en true;
    self.reduce_all_valid_files = reduce_all_valid_files

    # Limites de imagen. Se usan cuando resize esta activo
    self.max_img_width_px = max_img_width_px
    self.max_img_height_px = max_img_height_px

    self.output_reduce_prefix = output_reduce_prefix
    self.output_resize_prefix = output_resize_prefix
    self.best_prefix = best_prefix

    # Evitar sobreescribir imágenes originales
    if len(self.output_reduce_prefix) == 0:
      self.output_reduce_prefix = "IR_"

    if len(self.output_resize_prefix) == 0:
      self.output_resize_prefix = "R_"

    if len(self.best_prefix) == 0:
      self.best_prefix = "B_"

    # Solo se usa con resize_directory
    self.max_resize = max_resize

    # Opciones para gifs
    self.colors_= colors_
    self.scale_ratio = scale_ratio
    self.lossiness_factor = lossiness_factor


  def reduce_directory(self, path_to_directory, only_extensions=[]):

    temp_extensions = self.extensions

    # Temporarily limit the extensions to consider
    if len(only_extensions) > 0:
      self.extensions = only_extensions

    files_to_reduce = []

    if self.reduce_all_valid_files:
      files_to_reduce = self.all_valid_files(path_to_directory)
    else:
      files_to_reduce = self.files_above_threshold(path_to_directory)

    for size, file_path in files_to_reduce:
      self.reduce_image(file_path)

    # Restore the extensions to consider
    if len(only_extensions) > 0:
      self.extensions = temp_extensions


  def resize_limits_directory(self, path_to_directory, all=False):
    """Only resizes valid images to max width or max height specified."""
    files_to_resize=[]
    if all:
      files_to_resize = self.all_valid_files(path_to_directory)
    else:
      files_to_resize = self.files_above_threshold(path_to_directory)

    for size, file_path in files_to_resize:
      image = Image.open(file_path)
      if self.over_dimensions(image):
        output_path = self.insert_prefix(self.output_resize_prefix, file_path)

        if not os.path.exists(output_path):
            resized = self.reduce_dimensions(image)
            resized.save(output_path, optimize=True)
            self.display_result(output_path, file_path)
        else:
            self.display_result("exists", output_path)

      else:
        print(f"Info: image is within specified limit dimensions: {file_path}")


  def resize_directory(self, path_to_directory, only_extensions=[]):
    """Attempts to resize all valid files that are above threshold size."""

    temp_extensions = self.extensions

    if len(only_extensions) > 0:
        self.extensions = only_extensions

    files_to_resize = self.files_above_threshold(path_to_directory)

    for size, file_path in files_to_resize:
      self.resize_image(file_path)

    if len(only_extensions) > 0:
        self.extensions = temp_extensions


  def resize_image(self, path_to_file):
    """Calls resize function depending on file extension."""
    if not self.valid_file(path_to_file):
      print(f"Warning: file not valid {path_to_file}.")
      return

    output, input = "", ""

    if self.file_extension(path_to_file) in [".jpg", ".jpeg", ".png"]:
      output, input= self.resize_png_jpg(path_to_file)

    if self.file_extension(path_to_file) in [".gif"]:
      output, input = self.resize_gif(path_to_file)

    self.display_result(output, input)

  def resize_png_jpg(self, path_to_file):
    if self.file_extension(path_to_file) not in [".jpg", ".jpeg", ".png"]:
      print(f"Warning: invalid path for resize_png_jpg, {path_to_file}. Method will skip")
      return [path_to_file, path_to_file]

    image = Image.open(path_to_file)
    output_path = self.insert_prefix(self.output_resize_prefix, path_to_file)

    # Avoid processing an image again.
    if os.path.exists(output_path):
        return ["exists", output_path]

    is_png = self.file_extension(path_to_file) == ".png"

    resized_image = self.direct_resize(image, self.max_resize)

    if is_png:
      resized_image.save(output_path, optimize=True)
    else:
      resized_image.save(output_path, quality=80, optimize=True)

    return [output_path, path_to_file]


  def reduce_image(self, path_to_file):

    if not self.valid_file(path_to_file):
      print(f"Warning: file not valid {path_to_file}.")
      return

    output, input = "", ""

    if self.file_extension(path_to_file) in [".jpg", ".jpeg"]:
      output, input= self.reduce_jpg(path_to_file)
    elif self.file_extension(path_to_file) in [".png"]:
      output, input = self.reduce_png(path_to_file)
    elif self.file_extension(path_to_file) in [".gif"]:
      output, input = self.reduce_gif(path_to_file)

    self.display_result(output, input)


  def display_result(self, output, input):
    if output == "" or input == "":
      print(f"Info: file not processed {input}.")
    elif output == "exists":
      print(f"Info: skipping, file already exists {input}.")
    else:
      out_size = self.get_file_size_kb(output)
      in_size = self.get_file_size_kb(input)

      percentage = (out_size / in_size) * 100
      print(f"[{round(100 - percentage, 2)}% reduction | {in_size} kb -> {out_size} kb: {output}]")

      self.was_resized(output, input)

      if percentage == 100:
        print(f"Warning: file size unchanged for {output}.")
      if percentage > 100:
        print(f"WARNING: file size INCREASED for {output}.")
      if percentage < 100 and out_size > self.threshold_kb:
        print(f"Warning: file size reduced but image remains above theshold for {output}.")

  def was_resized(self, output_path, input_file):
    if os.path.basename(output_path).startswith(self.output_resize_prefix):
        input_image = Image.open(input_file)
        output_image = Image.open(output_path)
        print(f"Output: {output_image.width} w {output_image.height} h, Input: {input_image.width} w {input_image.height} h")


  def reduce_png(self, path_to_file):
    if self.file_extension(path_to_file) not in [".png"]:
      print(f"Warning: invalid path for reduce_png, {path_to_file}. Method will skip")
      return [path_to_file, path_to_file]

    image = Image.open(path_to_file)

    output_path = self.insert_prefix(self.output_reduce_prefix, path_to_file)

    if os.path.exists(output_path):
        return ["exists", output_path]

    reduced_png = image.copy()

    if self.resize:
      reduced_png = self.reduce_dimensions(reduced_png)

    reduced_png = reduced_png.quantize(colors=self.colors_png) # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize

    # PNG saving options: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#png
    reduced_png.save(output_path, optimize=True)
    return [output_path, path_to_file]


  def reduce_jpg(self, path_to_file):
    if self.file_extension(path_to_file) not in [".jpg", ".jpeg"]:
      print(f"Warning: invalid path for reduce_jpg, {path_to_file}. Method will skip")
      return [path_to_file, path_to_file]

    image = Image.open(path_to_file)

    reduced_jpg = image.copy()

    if self.resize:
      reduced_jpg = self.reduce_dimensions(reduced_jpg)

    # JPEG saving options: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg-saving

    output_path = self.insert_prefix(self.output_reduce_prefix, path_to_file)

    if os.path.exists(output_path):
        return ["exists", output_path]

    reduced_jpg.save(output_path)

    initial_quality = 90
    current_quality = initial_quality
    quality_interval = int((initial_quality - self.min_quality) / 5) # Check 5 intervals

    while self.get_file_size_kb(output_path) > self.threshold_kb and current_quality >= self.min_quality and quality_interval > 0:
      reduce_iteration = reduced_jpg.copy()

      reduce_iteration.save(output_path, optimize=True, quality=current_quality)
      current_quality -= quality_interval

    return [output_path, path_to_file]


  def reduce_dimensions(self, image):
    """Reduces image to max dimensions. Maintains aspect ratio: considers only max_img_width_px or max_img_height_px."""
    reduced_dim = image.copy()

    try:
      if reduced_dim.width > self.max_img_width_px and self.max_img_width_px > 0:
        width_reduction = self.max_img_width_px / image.width
        return self.direct_resize(reduced_dim, width_reduction)

      if reduced_dim.height > self.max_img_height_px and self.max_img_height_px > 0:
        height_reduction = self.max_img_height_px / image.height
        return self.direct_resize(reduced_dim, height_reduction)

    except:
      print("Error: Some error happened during resizing.")

    print(f"Warning: reduce_dimensions didn't modify the image. original: width({image.width}), height ({image.height}). Max dimensions: width({self.max_img_width_px}), height ({self.max_img_height_px})")
    return reduced_dim


  def reduce_gif(self, path_to_file):
    if self.file_extension(path_to_file) not in [".gif"]:
      print(f"Warning: invalid path for reduce_gif, {path_to_file}. Method will skip")
      return [path_to_file, path_to_file]

    output_path = self.insert_prefix(self.output_reduce_prefix, path_to_file)
    return self.modify_gif(path_to_file, output_path, change_scale=False, change_quality=True)


  def resize_gif(self, path_to_file):
    if self.file_extension(path_to_file) not in [".gif"]:
      print(f"Warning: invalid path for resize_gif, {path_to_file}. Method will skip")
      return [path_to_file, path_to_file]

    output_path = self.insert_prefix(self.output_resize_prefix, path_to_file)
    return self.modify_gif(path_to_file, output_path, change_scale=True, change_quality=False)


  def modify_gif(self, path_to_file, output_path, change_scale=False, change_quality=False):
    options_string = ["--verbose"]

    # Avoid processing an image again.
    if os.path.exists(output_path):
        return ["exists", output_path]

    if change_quality:
      options_string.append(f"--lossy={self.lossiness_factor}")

    if change_scale:
      scale_factor = f'{self.scale_ratio}x{self.scale_ratio}'
      options_string.append(f"--scale={scale_factor}")

    pygifsicle.gifsicle(
      sources=[path_to_file], # or a single_file.gif
      destination=output_path, # or just omit it and will use the first source provided.
      optimize=True, # Whetever to add the optimize flag of not
      colors=self.colors_, # Number of colors to use
      options=options_string # Options to use.
    )

    return [output_path, path_to_file]


  def over_dimensions(self, image):
    return image.width > self.max_img_width_px or image.height > self.max_img_height_px


  def direct_resize(self, image, ratio):
    new_width = int(image.width * ratio)
    new_height = int(image.height * ratio)
    resized_image = image.resize((new_width, new_height))
    # See resampling filters: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#PIL.Image.Resampling.LANCZOS
    return resized_image


  def file_extension(self, path_to_file):
    _, ext = os.path.splitext(path_to_file)
    return ext


  def valid_file(self, path_to_file):
    file_ext = self.file_extension(path_to_file)
    return file_ext in self.extensions


  def files_above_threshold(self, path_to_directory):
    return self.all_valid_files(path_to_directory, self.threshold_kb)


  def all_valid_files(self, path_to_directory, threshold_kb_=0):
    valid_files = []
    for root, _, files in os.walk(path_to_directory):
      for file in files:
        file_path = os.path.join(root, file)

        if not self.valid_file(file_path):
          continue

        size = self.get_file_size_kb(file_path)
        if (size >= threshold_kb_):
          valid_files.append((size, file_path))

    list.sort(valid_files, reverse=True)
    return valid_files


  def print_files_above_threshold(self, path_to_directory):
    files_over_threshold = self.files_above_threshold(path_to_directory)
    for file in files_over_threshold:
      print(f"{file[0]} KB: {file[1]}")


  def generated_files(self, path_to_directory):
    generated_files = []
    for root, _, files in os.walk(path_to_directory):
      for file in files:
        file_path = os.path.join(root, file)

        if not self.valid_file(file_path):
          continue

        if self.file_was_generated(file):
          size = self.get_file_size_kb(file_path)
          generated_files.append((size, file_path))

    list.sort(generated_files, reverse=True)
    return generated_files


  def file_was_generated(self, path_to_file):
    file_basename = os.path.basename(path_to_file)
    return file_basename.startswith(self.output_reduce_prefix) or file_basename.startswith(self.output_resize_prefix) or file_basename.startswith(self.best_prefix)


  def insert_prefix(self, prefix, path_to_file):
    directory = os.path.dirname(path_to_file)
    filename = prefix + os.path.basename(path_to_file)
    return os.path.join(directory, filename)


  def print_generated_files(self, path_to_directory, only_above_threshold=False):
    below_threshold = 0
    generated_files = self.generated_files(path_to_directory)

    for file in generated_files:
      if (file[0] < self.threshold_kb):
        below_threshold += 1

    if len(generated_files) == 0:
      print("No generated files found.")
      return

    percentage = int((below_threshold / len(generated_files)) * 100)
    print(f'{percentage}% of generated files are below threshold')

    for file in generated_files:
      if only_above_threshold and file[0] < self.threshold_kb:
         break
      print(f"[{file[0]} KB]: {file[1]}")


  def get_file_size_kb(self, file_path):
    size = os.path.getsize(file_path)
    return size // 1024  # bytes a kb


  def move_generated(self, directory_path, output_directory, only_basename=False):
    generated_files = self.generated_files(directory_path)

    destination_directory = os.path.dirname(output_directory)
    os.makedirs(destination_directory, exist_ok=True)

    for file in generated_files:
      destination_path = ""

      if self.is_contained(output_directory, file[1]):
        print(f"Info: {file[1]} is contained in {output_directory}. Skipping.")
        continue

      if only_basename:
        destination_path = os.path.join(output_directory, os.path.basename(file[1]))
      else:
        destination_path = os.path.join(output_directory, file[1])
        destination_directory = os.path.dirname(destination_path)

        os.makedirs(destination_directory, exist_ok=True)

      shutil.move(file[1], destination_path)

      print(f"Info: moved {file[1]} to {destination_path}.")


  def is_contained(self, directory_path, file_path):
    directory_path = os.path.abspath(directory_path)
    file_path = os.path.abspath(file_path)
    return file_path.startswith(directory_path + os.sep)


  def check_remaining_files(self, directory_path):
    generated_files, original_files = self.generated_and_original(directory_path)
    original_set = set()

    # Save original basenames of files that are above threshold.
    for file in original_files:
      if file[0] > self.threshold_kb:
        original_set.add(os.path.basename(file[1]))

    for file in generated_files:
      if file[0] < self.threshold_kb:
        original_name = self.trim_prefix(file[1])

        if original_name in original_set:
          original_set.remove(original_name)

    if len(original_set) == 0:
      print(f"There is at least one version of each file that is below {self.threshold_kb} kb.")
    else:
      print(f"There are {len(original_set)} files that are above {self.threshold_kb} kb and have no generated version.")
      for file in original_set:
        print(f"  {file}")


  def generated_and_original(self, directory_path):
    all_files = self.all_valid_files(directory_path)
    generated_files = []
    original_files = []
    for file in all_files:
      if self.file_was_generated(file[1]):
        generated_files.append(file)
      else:
        original_files.append(file)

    return generated_files, original_files


  def trim_prefix(self, path_to_file):
    basename = os.path.basename(path_to_file)
    if basename.startswith(self.output_reduce_prefix):
      return self.trim_prefix(basename[len(self.output_reduce_prefix):])
    elif basename.startswith(self.output_resize_prefix):
      return self.trim_prefix(basename[len(self.output_resize_prefix):])
    elif basename.startswith(self.best_prefix):
      return self.trim_prefix(basename[len(self.best_prefix):])

    return basename


  def modify_gif_options(self, colors_: int, scale_ratio: str, lossiness_factor: str):
    self.colors_= colors_
    self.scale_ratio = scale_ratio
    self.lossiness_factor = lossiness_factor


  # Only method that can remove files. Maintains original files.
  def save_only_smallest_modified_files(self, directory_path):
    for root, _, files in os.walk(directory_path):
      for file in files:

        file_path = os.path.join(root, file)

        if not self.valid_file(file_path) or not self.file_was_generated(file_path):
          continue

        original_path = os.path.join(root, self.trim_prefix(file_path))

        best_path = self.insert_prefix(self.best_prefix, original_path)

        if not os.path.exists(best_path):
          shutil.move(file_path, best_path)
          continue

        if self.get_file_size_kb(file_path) < self.get_file_size_kb(best_path):
          shutil.move(file_path, best_path)
        else:
          os.remove(file_path)