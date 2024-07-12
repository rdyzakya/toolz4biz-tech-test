from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import math
from .scrape_utils import *


def get_direction_speech(origin, destination, headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")  # Optional: useful for headless mode on Windows
        chrome_options.add_argument("--no-sandbox")   # Optional: useful for running as root on Linux
    
    driver = webdriver.Chrome(options=chrome_options)
    
    scrape_utils.loop_function(driver.get, "https://maps.google.com/?hl=en")

    # Find the search bar using the class name
    search_bar = scrape_utils.loop_function(driver.find_element, By.CLASS_NAME, "searchboxinput")

    scrape_utils.loop_function(search_bar.send_keys, destination)
    scrape_utils.loop_function(search_bar.send_keys, Keys.ENTER)

    try:
        all_place = scrape_utils.loop_function(driver.find_elements, By.CLASS_NAME, "Nv2PK", length_non_zero=True)
        scrape_utils.loop_function(all_place[0].click)
    except:
        pass

    # Find all buttons with the class "g88MCb S9kvJb"
    buttons = scrape_utils.loop_function(driver.find_elements, By.CLASS_NAME, "g88MCb.S9kvJb", length_non_zero=True)

    # Initialize variable to store the target button
    directions_button = None

    # Iterate through the buttons to find the one with the desired data-value
    for button in buttons:
        data_value = scrape_utils.loop_function(button.get_attribute, "data-value")
        if data_value in ["Rute", "Directions"]:
            directions_button = button
            break
    
    scrape_utils.loop_function(directions_button.click)

    # Construct XPath to find the button with specific child img
    xpath_expression = "//button[contains(@class, 'm6Uuef')]//img[@aria-label='Mengemudi' or @aria-label='Driving']/parent::button"

    # Find the button using XPath
    driving_option_button = scrape_utils.loop_function(driver.find_element, By.XPATH, xpath_expression)

    scrape_utils.loop_function(driving_option_button.click)

    # Input origin
    search_input = scrape_utils.loop_function(driver.find_elements, By.CLASS_NAME, "tactile-searchbox-input", length_non_zero=True)

    scrape_utils.loop_function(search_input[0].click)
    scrape_utils.loop_function(search_input[0].send_keys, origin)
    scrape_utils.loop_function(search_input[0].send_keys,Keys.ENTER)

    # get all directions
    all_directions = scrape_utils.loop_function(driver.find_elements, By.CLASS_NAME, "UgZKXd.clearfix.yYG3jf", length_non_zero=True)

    minimum_duration = math.inf
    chosen_direction = None
    duration_text = None
    distance_text = None
    chosen_idx = 0
    for i in range(len(all_directions)):
        duration = scrape_utils.loop_function(all_directions[i].find_element, By.CLASS_NAME, "Fk3sm").text
        # total_distance = all_directions[i].find_element(By.CLASS_NAME, "ivN21e.tUEI8e.fontBodyMedium")

        duration_value = scrape_utils.calculate_duration(duration)

        if duration_value < minimum_duration:
            minimum_duration = duration_value
            chosen_direction = all_directions[i]
            duration_text = duration
            distance_text = scrape_utils.loop_function(chosen_direction.find_element, By.CLASS_NAME, "ivN21e.tUEI8e.fontBodyMedium").text
            chosen_idx = i
    if chosen_idx != 0:
        scrape_utils.loop_function(chosen_direction.click)

    detail_button = scrape_utils.loop_function(chosen_direction.find_element, By.CLASS_NAME, "TIQqpf.fontTitleSmall.XbJon.Hk4XGb")

    scrape_utils.loop_function(detail_button.click)

    direction_dict = {}

    direction_step_1 = scrape_utils.loop_function(driver.find_elements, By.CLASS_NAME, "FueNo", length_non_zero=True)

    for dir in direction_step_1:
        scrape_utils.loop_function(dir.click)
        is_toggle_down = True
        try:
            parent_text = scrape_utils.loop_function(dir.find_element, By.CLASS_NAME, "JoXhkf.fontBodyMedium").text
        except NoSuchElementException:
            parent_text = scrape_utils.loop_function(dir.find_element, By.CLASS_NAME, "j3isMd").text
            is_toggle_down = False

        parent_time_distance = scrape_utils.loop_function(dir.find_element, By.CLASS_NAME, "directions-mode-distance-time.fontBodySmall").text

        direction_dict[(parent_text, parent_time_distance)] = []

        if is_toggle_down:

            child_directions = scrape_utils.loop_function(dir.find_elements, By.CLASS_NAME, "S0JAMb", length_non_zero=True)

            for cd in child_directions:
                # cd_text = cd.find_element(By.CLASS_NAME, "fInDkc.fontBodyMedium").text
                cd_text = scrape_utils.loop_function(cd.find_element, By.CLASS_NAME, "j3isMd").text
                cd_time_distance = scrape_utils.loop_function(cd.find_element, By.CLASS_NAME, "directions-mode-distance-time.fontBodySmall").text
                direction_dict[(parent_text, parent_time_distance)].append((cd_text, cd_time_distance))
    
    driver.quit()

    speech = scrape_utils.create_direction_speech(origin, destination, distance_text, duration_text, direction_dict)

    return speech