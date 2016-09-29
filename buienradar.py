from PIL import Image
import subprocess
import time
import os

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
    out = "\n" * 25

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
              "104": (50, 50, 255),
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


# Download the image
subprocess.check_call(
    ["wget", "http://api.buienradar.nl/image/1.0/RadarMapNL?w=%i&h=%i" % image_size, "-O", "temp.gif"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Let's hope wget doesn't give an error, a good programmer might check for this.
img = Image.open("temp.gif")

# Set the time between frames in seconds
frame_time = 1

# Draw loop, can be quit with Ctrl + c
try:
    while True:
        draw_gif(img)
        time.sleep(frame_time)
except KeyboardInterrupt:
    print("\033[0m\nShutting Down!")

# Close and remove temp gif file
img.close()
os.remove("temp.gif")
