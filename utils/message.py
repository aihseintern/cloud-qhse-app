# whatsapp_sender.py
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os
import re
import logging
from colorama import Back, Style, init
from termcolor import colored
import flask_mail
import platform
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService

load_dotenv()

class SeleniumManager:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.actions = None

    def initialize_driver(self):
        pass

    def get_driver(self):
        if self.driver is None:
            self.initialize_driver()
        return self.driver

    def get_wait(self):
        if self.wait is None:
            self.initialize_driver()
        return self.wait
    
    def get_actions(self):
        if self.actions is None:
            self.initialize_driver()
        return self.actions

    def quit_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None  
            self.actions = None  

class ReportManager(SeleniumManager):
    def __init__(self):
        super().__init__()

    def initialize_driver(self):        
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
        firefox_options = Options()
        firefox_options.add_argument('--headless')
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(os.getenv("FIREFOX_PROFILE_DIR"))
        self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)
        # self.driver = webdriver.Firefox(options=firefox_options)
        self.driver.get("https://web.whatsapp.com/")
        self.wait = WebDriverWait(self.driver, 150)
        self.actions = ActionChains(self.driver)        
        mail_manager.refresh_and_send("report_manager")  
    
class OTPManager(SeleniumManager):
    def __init__(self):
        super().__init__()

    def initialize_driver(self):
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
        firefox_options = Options()
        # firefox_options.add_argument('--headless')
        firefox_options.add_argument("-profile")
        firefox_options.add_argument(os.getenv("FIREFOX_PROFILE_DIR"))
        self.driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)
        # self.driver = webdriver.Firefox(options=firefox_options)
        self.driver.get("https://web.whatsapp.com/")
        self.wait = WebDriverWait(self.driver, 150)
        self.actions = ActionChains(self.driver)        
        mail_manager.refresh_and_send("report_manager")       

report_selenium_manager = ReportManager()
otp_selenium_manager = OTPManager()

class MailManager:
    def __init__(self):
        # Barcode path
        self.barcode_path = '/html/body/div[1]/div/div/div[2]/div[3]/div[1]'
        self.previous_data_ref = None
        self.selenium_manager = None
        
    def init_app(self, app):
        self.app = app
        print(Back.MAGENTA)
        print("Mail Manager initialized.")
        print(Style.RESET_ALL)
        print(f"self app: {self.app}")
        print(f"app: {app}")
        
    def send_barcode(self, selenium_manager):
        try:
            barcode = self.selenium_manager.wait.until(EC.presence_of_element_located((By.XPATH, self.barcode_path)))  # Update this line
            barcode_img = barcode.screenshot_as_png
            with open('barcode.png', 'wb') as f:
                f.write(barcode_img)
                print(colored("Barcode image saved.", "white", "on_blue"))
            
            # Send the barcode image via email
            subject = f"Your Whatsapp Barcode from {selenium_manager}"
            recipient = 'aihseintern@gmail.com'  # Get recipient email from environment variable
            body = "Please find the attached barcode image."
            
            with open('barcode.png', 'rb') as f:
                msg = flask_mail.Message(subject, sender=os.getenv('MAIL_USERNAME'), recipients=[recipient])
                msg.body = body
                msg.attach('barcode.png', 'image/png', f.read())
                print(colored("Barcode image attached to email.", "white", "on_blue"))
            
            with self.app.app_context():
                print(colored("Sending barcode...", "white", "on_blue"))
                from app import mail
                mail.send(msg)
                print(colored("Barcode sent successfully.", "white", "on_blue"))
            
            print(Back.GREEN)
            print("Barcode sent successfully!")
            print(Style.RESET_ALL)
            return "Barcode sent successfully!"
        
        except Exception as e:
            print(colored(f"Failed to send barcode: {e}", "white", "on_red"))
            return f"Failed to send barcode: {e}"

    def refresh_and_send(self, selenium_manager):
        last_refresh = time.time()
        self.selenium_manager = report_selenium_manager if selenium_manager == "report_manager" else otp_selenium_manager
        print("last_refresh: ", last_refresh)
        
        while True:
            if time.time() - last_refresh > 50:
                self.selenium_manager.driver.refresh()
                last_refresh = time.time()
            time.sleep(1)
            try:
                barcode_element = self.selenium_manager.driver.find_element("xpath", '//div[@class="_akau"]')
                current_data_ref = barcode_element.get_attribute("data-ref")
                if current_data_ref != self.previous_data_ref:
                    self.send_barcode(selenium_manager)
                    self.previous_data_ref = current_data_ref
            except Exception as e:
                self.previous_data_ref = None
                print(Back.RED)
                logging.info(f"Barcode scanned successfully, element not found", {e})
                print(Style.RESET_ALL)
                return
            
mail_manager = MailManager()

# WA Message Path
# WA Path
class Message:
    def __init__(self, message_template, detected_object):
        self.message_template = message_template
        self.detected_object = detected_object

    def render(self):
        # Replace placeholders in the template with actual data from detected_object
        rendered_message = self.message_template
        
        for key, value in self.detected_object.items():
            placeholder = "@" + key
            # print("Placeholder: ", placeholder)
            rendered_message = rendered_message.replace(placeholder, str(value))

        # Remove any remaining placeholders that were not replaced
        rendered_message = re.sub(r'\{\{.*?\}\}', '', rendered_message)
        
        return rendered_message
    
    @staticmethod
    def send_whatsapp_message(target_name, message, image_path):
        driver = report_selenium_manager.get_driver()
        wait = report_selenium_manager.get_wait()
        actions = report_selenium_manager.get_actions()

        try:
            #path update 15 oct 10.32
            print(driver.page_source)

            # contact_path = f'//span[contains(@title, "eh")]'
            contact_path = f'//span[@title="{target_name}"]'       
            contact = wait.until(EC.presence_of_element_located((By.XPATH, contact_path)))
            contact.click()

            text_box_xpath = '/html/body/div[1]/div/div/div[2]/div[4]/div/footer/div[1]/div/span/div/div[2]/div[1]/div/div[1]'
            text_box = wait.until(EC.presence_of_element_located((By.XPATH, text_box_xpath)))
            
            # Split the message into lines
            lines = message.split('\n')
            
            # Move to the text box and type each line followed by pressing Enter
            actions.move_to_element(text_box).click()  # Click on the text box to focus
            
            for i, line in enumerate(lines):
                actions.send_keys(line)  # Type the current line
                
                # If it's not the last line, press Shift + Enter
                if i < len(lines) - 1:
                    actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
                    
            # After typing all lines
            actions.perform()  # Execute all actions

            if image_path:
                attachment_button_xpath = '/html/body/div[1]/div/div/div[2]/div[4]/div/footer/div[1]/div/span/div/div[1]/div/div/div'
                attachment_button = wait.until(EC.presence_of_element_located((By.XPATH, attachment_button_xpath)))

                attachment_button.click()
                
                image_button_xpath = '/html/body/div[1]/div/div/div[2]/div[4]/div/footer/div[1]/div/span/div/div[1]/div/div/span/div/ul/div/div[2]/li/div/input'
                image_button = wait.until(EC.presence_of_element_located((By.XPATH, image_button_xpath)))

                image_button.send_keys(image_path)

                send_button_xpath = '/html/body/div[1]/div/div/div[2]/div[2]/div[2]/span/div/div/div/div[2]/div/div[2]/div[2]/div/div'
                send_button = wait.until(EC.presence_of_element_located((By.XPATH, send_button_xpath)))

                send_button.click()
                # actions.move_to_element(text_box).send_keys(Keys.ESCAPE).send_keys(Keys.ESCAPE).send_keys(Keys.ESCAPE).perform()
            else:
                actions.move_to_element(text_box).send_keys(Keys.RETURN).perform()
                actions.move_to_element(text_box).send_keys(Keys.ESCAPE).send_keys(Keys.ESCAPE).send_keys(Keys.ESCAPE).perform()
                
        except Exception as e:
            logging.error(f"Error while sending WhatsApp message: {e}")
            # Tambahkan penanganan kesalahan di sini jika diperlukan

class OTPMessage:
    def __init__(self, phone_number, message):
        self.phone_number = phone_number
        self.message = message

    def send(self):
        driver = otp_selenium_manager.get_driver()
        wait = otp_selenium_manager.get_wait()
        actions = otp_selenium_manager.get_actions()

        try:
            driver.get("https://web.whatsapp.com/send?phone=" + self.phone_number + "&text=" + self.message)
            time.sleep(5)
            text_box_xpath = '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div/div'
            text_box = wait.until(EC.presence_of_element_located((By.XPATH, text_box_xpath)))
            actions.move_to_element(text_box).send_keys(Keys.RETURN).perform()
        except Exception as e:
            logging.error(f"Error while sending OTP: {e}")
            # Tambahkan penanganan kesalahan di sini jika diperlukan
