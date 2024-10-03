import time
from pimoroni import Button, RGBLED
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
from pimoroni_i2c import PimoroniI2C

# Initialize the display
display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2)

# Initialize buttons
button_a = Button(12)  # Adjust GPIO pins as necessary
button_b = Button(13)
button_x = Button(14)
button_y = Button(15)

# Initialize RGB LED (on Pico Display 2.0)
rgb_led = RGBLED(6, 7, 8)  # GPIO pins for red, green, blue LEDs

# Create pens for blue, dark blue, and white colors
blue_pen = display.create_pen(0, 0, 255)       # Bright blue for menu background
dark_blue_pen = display.create_pen(0, 0, 100)  # Dark blue for selected menu item
white_pen = display.create_pen(255, 255, 255)  # White for text

# Menu items with blue background for all
menu_items = [
    {"name": "Temperature"},
    {"name": "Pressure"},
    {"name": "Humidity"},
    {"name": "Light"},
    {"name": "Proximity"},
    {"name": "Orientation"},
    {"name": "Motion"}
]

current_selection = 0  # Start with the first menu item
in_sensor_display = False  # Flag to determine if we're in sensor display mode

# The actual dimensions of the Pico Display 2.0 (320x240)
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

# Initialize Pimoroni I2C for all sensors
print("Initializing sensors...")
i2c = PimoroniI2C(sda=4, scl=5)  # Using Breakout Garden pins (SDA on pin 4, SCL on pin 5)
bme280 = BreakoutBME280(i2c)
ltr559 = BreakoutLTR559(i2c)     # Initialize the LTR-559 sensor
motion_sensor = LSM6DS3(i2c, mode=NORMAL_MODE_104HZ)  # LSM6DS3 on the same I2C bus

# Check LTR-559 part ID to confirm the sensor is connected
part_id = ltr559.part_id()
print("Found LTR559. Part ID: 0x", '{:02x}'.format(part_id), sep="")

def draw_menu():
    display.set_pen(0)  # Set pen to black for the background
    display.clear()     # Clear the display

    # Calculate the vertical spacing for each item
    item_spacing = DISPLAY_HEIGHT // len(menu_items)  # Divide total height by number of items

    # Loop through menu items and display them
    for i, item in enumerate(menu_items):
        if i == current_selection:
            # Highlight selected item with dark blue
            display.set_pen(dark_blue_pen)
        else:
            # Use blue background for unselected items
            display.set_pen(blue_pen)

        # Draw a full-width rectangle for each menu item
        display.rectangle(0, i * item_spacing, DISPLAY_WIDTH, item_spacing)

        # Set the pen to white for text
        display.set_pen(white_pen)
        display.text(item["name"], 10, i * item_spacing + 10, scale=3)

    display.update()

def display_sensor(sensor_name):
    display.set_pen(0)  # Set pen to black for the background
    display.clear()

    # Read sensor data from the BME280
    bme_reading = bme280.read()  # BME280 returns a tuple (temperature, pressure, humidity)

    # Get the LTR-559 readings
    ltr_reading = ltr559.get_reading()

    if ltr_reading is None:
        light = None
        proximity = None
    else:
        light = ltr_reading[BreakoutLTR559.LUX]  # Ambient light in lux
        proximity = ltr_reading[BreakoutLTR559.PROXIMITY]  # Proximity reading

    # Access the BME280 data by indices
    temperature = bme_reading[0]
    pressure = bme_reading[1]
    humidity = bme_reading[2]

    # Get the motion sensor readings (accelerometer and gyroscope)
    ax, ay, az, gx, gy, gz = motion_sensor.get_readings()

    # Determine what to display based on the selected sensor
    if sensor_name == "Temperature":
        label = "Temperature:"
        value = f"{temperature:.2f} C"
    elif sensor_name == "Pressure":
        label = "Pressure:"
        value = f"{pressure / 100:.2f} hPa"  # Convert to hPa
    elif sensor_name == "Humidity":
        label = "Humidity:"
        value = f"{humidity:.2f} %"
    elif sensor_name == "Light":
        label = "Ambient Light:"
        value = f"{light:.2f} lux" if light is not None else "No data"
    elif sensor_name == "Proximity":
        label = "Proximity:"
        value = f"{proximity}" if proximity is not None else "No data"
    elif sensor_name == "Orientation":
        label = "Orientation (Accel):"
        value = f"X:{ax:.2f}\nY:{ay:.2f}\nZ:{az:.2f}"
    elif sensor_name == "Motion":
        label = "Motion (Gyro):"
        value = f"X:{gx:.2f}\nY:{gy:.2f}\nZ:{gz:.2f}"
    else:
        label = "Sensor not available"
        value = ""

    # Display label on one line and the value on the next line, with larger font for the value
    display.set_pen(white_pen)
    display.text(label, 10, 40, scale=2)  # Label on the first line
    display.text(value, 10, 80, scale=3)  # Value on the second line, larger font
    display.update()

# Main loop
while True:
    if not in_sensor_display:
        draw_menu()  # Show the menu

        # Button press handling for navigation
        if button_x.is_pressed:
            current_selection = (current_selection - 1) % len(menu_items)
            time.sleep(0.3)  # Debouncing
        elif button_y.is_pressed:
            current_selection = (current_selection + 1) % len(menu_items)
            time.sleep(0.3)  # Debouncing
        elif button_b.is_pressed:
            in_sensor_display = True  # Switch to sensor display mode
            selected_sensor = menu_items[current_selection]["name"]
            time.sleep(0.3)  # Debouncing
        elif button_a.is_pressed:
            pass  # No action for Button A in the main menu
    else:
        display_sensor(selected_sensor)  # Display the selected sensor

        # Check if the user wants to go back to the menu
        if button_a.is_pressed:
            in_sensor_display = False  # Return to the main menu
            time.sleep(0.3)  # Debouncing

