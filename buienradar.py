from PIL import Image
import subprocess
import time
import datetime
import os
import io
import threading

# Set the image size constants used in drawing and getting the image
image_size = (70 * 2, 55)
image_width, image_height = image_size


# This function draws the next frame of the gif
def draw_gif(image):
    global image_width, image_heigth

    # Skip ahead and return to start if we reach EOF
    try:
        image.seek(image.tell() + 1)
    except EOFError:
        image.seek(0)

    # Convert image to RGB
    rgb_im = image.convert('RGB')

    # Append newlines so we can't see the old frame
    out = "\n" * 27

    # Generate the image string
    for y in range(image_height):
        for x in range(image_width):
            color_code = get_closest_color(rgb_im.getpixel((x, y)))
            out += "\033[%sm " % (color_code)
        out += "\033[49m\n"  # reset color

    # Print the image
    print(out)


# Gets the color distance between two RGB values. This is a linear calculation, no fancy math.
def get_color_distance(rgb1, rgb2):
    (r1, g1, b1) = rgb1
    (r2, g2, b2) = rgb2
    return abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)


# Gets the ANSI color in our dictionary that is closest to the RGB value given.
def get_closest_color(rgb):
    # These RGB values are just a guess ;)
    colors = {"40": (0, 0, 0),
              "41": (255, 0, 0),
              "42": (0, 255, 0),
              "43": (255, 255, 0),
              "44": (0, 0, 255),
              "45": (255, 0, 255),
              "46": (0, 255, 255),
              "47": (255, 255, 255),
              "104": (70, 70, 255),
              "48;5;18": (0, 0, 160),
              "48;5;22": (0, 50, 0)
              }

    # Loop over all the keys and get the smallest distance between the rgb values.
    closest, cdistance = "40", get_color_distance(colors["40"], rgb)
    for key in colors:
        color = colors[key]
        distance = get_color_distance(color, rgb)
        if distance < cdistance:
            closest, cdistance = key, distance

    # Return the closest ANSI value
    return closest

def format_time_diff(previous_time):
    current_time = datetime.datetime.now()
    time_diff = current_time - previous_time

    seconds_diff = time_diff.total_seconds()
    if seconds_diff < 60:
        time_ago = int(seconds_diff)
        unit = "seconden"
    else:
        minutes_diff = seconds_diff / 60
        time_ago = int(minutes_diff)
        unit = "minuten"

    return f"Beelden {time_ago} {unit} geleden opgehaald"


# loop to render everything that needs to be displayed on the screen
def render(img, is_thread_active, last_data_received_datetime):
    frame_time = 1
    while is_thread_active:
        draw_gif(img)
        print(format_time_diff(last_data_received_datetime))
        time.sleep(frame_time)

# amount of seconds between buienradar api calls
GIF_GET_INTERVAL_SECONDS = 120
thread = threading.Thread()
try:
    while True:
        last_data_received_datetime = datetime.datetime.now()
        # Get buienradar gif from the api, write to STDOUT
        gif_get_process = subprocess.Popen(
            ["wget", "http://api.buienradar.nl/image/1.0/RadarMapNL?w=%i&h=%i" % image_size, "--output-document=-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        # make a stream from the wget process stdout bytes, and create a PIL image
        image_bytes = gif_get_process.stdout.read()
        image_stream = io.BytesIO()
        image_stream.write(image_bytes)
        img = Image.open(image_stream)

        # spawn a thread that renders the image to terminal while the main thread sleeps
        is_thread_active = True
        thread = threading.Thread(target=render, args=(img, is_thread_active, last_data_received_datetime))
        thread.start()
        
        time.sleep(GIF_GET_INTERVAL_SECONDS)
        is_thread_active = False
        if thread.is_alive():
            thread.join()
        
except KeyboardInterrupt:
    print("\033[0m\nShutting Down!")
    is_thread_active = False
    if thread.is_alive():
        thread.join()