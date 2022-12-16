import configparser
import time
import argparse
from playwright.sync_api import sync_playwright, Page, FrameLocator, expect

# initialise and read the configuration file
config = configparser.ConfigParser()
config.read('credentials.ini')

# Credentials
username = config.get('credentials', 'email')
password = config.get('credentials', 'password')
au_username = config.get('credentials', 'au_username')
account_id = config.get('credentials', 'account_id')
asset_id = config.get('credentials', 'asset_id')
aws_pwd = ""

# Initial Input
def take_input(text : str):
    choice_input = input(text)
    return choice_input

# Parse CMD Choice
def arg_parser():
    parser = argparse.ArgumentParser(
        description= "Automates Password Retrieval from Beyond Trust Vault."
    )
    parser.add_argument(
        "-d", "--domain", help="Domain to generate password for.", type=str, default="qarft"
    )
    args = parser.parse_args()
    return args

# domain-choice can be (qarft,dvrft,prrft)
argument_choice = arg_parser()
domain_choice = argument_choice.domain

# Domain check util
def domain_avail_flag(domain_choice: str):
    if(domain_choice.lower() == "dvrft"):
        return 1
    elif(domain_choice.lower() == "qarft"):
        return 2
    elif(domain_choice.lower() == "prrft"):
        return 3
    else:
        return -1

# Write Credentials to files
def write_to_file(val: str, domain:str):
    print("Writing credentials to file aws_credentials.ini")
    with open('aws_credentials.ini', 'r') as file:
        data = file.readlines()
    if(domain == "qarft"):
        data[1] = f'qarft_password = {val}\n'
    elif(domain == "dvrft"):
        data[2] = f'dvrft_password = {val}\n'
    else:
        data[3] = f'prrft_password = {val}\n'
    with open('aws_credentials.ini', 'w') as file:
        file.writelines( data )
           
def browser_initialisation(playwright: sync_playwright):
    browser = playwright.chromium.launch(headless = False)
    page : Page = browser.new_page()
    page.set_default_timeout(0)
    page.goto("https://pam.int.refinitiv.com/WebConsole//#!/passwordsafe/home")
    return page

def aws_browser_initialisation(playwright: sync_playwright):
    browser = playwright.chromium.launch(headless=False)
    aws_page : Page = browser.new_page()
    aws_page.set_default_timeout(0)
    aws_page.goto("https://myapplications.microsoft.com/")
    return aws_page

def open_and_login(page: Page):
    page.get_by_placeholder('Username').fill(username)
    page.get_by_placeholder('Password').fill(password)
    page.locator('.button-label.unselectable.ng-binding').click()

def get_frame(page: Page, frame_id: str):
    frame = page.frame_locator(frame_id)
    return frame

def blm_access(frame: FrameLocator):
    frame.locator(".message").wait_for(state='visible')
    frame.locator(".btn.btn-secondary.Domain.Linked.Accounts").click()
    frame.locator("text='Click here to return all accounts'").click()

# Check availability of passwords
def check_availability(selector: str ,frame: FrameLocator):
    print("Checking Domain Availability...")
    baseTable = frame.locator(selector)
    text_content = baseTable.text_content(timeout= 0)
    if(text_content == "Not available"):
        return False
    else:
        return True

def aws_page_access(aws_page: Page):
    domain = generate_domain()
    password = generate_password()
    aws_page.locator("//input[@placeholder='Email, phone, or Skype']").fill(au_username + domain)
    aws_page.locator("//input[@value='Next']").click()
    aws_page.locator("//input[@placeholder='Password']").fill(password)
    aws_page.locator("//input[@value='Sign in']").click()
    aws_page.locator("//input[@type='button']").click()
    aws_page.locator("//body[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]").click()
    aws_page.bring_to_front()
    aws_page.locator(f"//input[@value='arn:aws:iam::{account_id}:role/human-role/{asset_id}-Developer']").click()
    aws_page.locator("//a[@value='Continue']").click()
    
    
# Utils to generate domain email and password
def generate_domain():
    if domain_choice == "qarft":
        return "@qarft.refinitiv.com"
    elif domain_choice == "dvrft":
        return "@dvrft.refinitiv.com"
    elif domain_choice == "prrft":
        return "@prrft.refinitiv.com"
    
def generate_password():
    aws_config = configparser.ConfigParser()
    aws_config.read('aws_credentials.ini')
    if domain_choice == "qarft":
        return aws_config.get('AWS', 'qarft_password')
    elif domain_choice == "dvrft":
        return aws_config.get('AWS', 'dvrft_password')
    elif domain_choice == "prrft":
        return aws_config.get('AWS', 'prrft_password')

# User Choice (AWS Console)
def proceed_choice():
    choice = take_input("Open AWS Console? (yes/no): ")
    if(choice.lower() == "yes"):
        aws_page = aws_browser_initialisation(playwright)
        aws_page_access(aws_page)
        aws_page.pause()
    elif(choice.lower() == "no"):
        print("exit")
    else:
        print("Invalid Choice")
        
def submit_request(domain: str, frame: FrameLocator, page: Page):
    button = frame.locator("//button[contains(text(),'Submit Request')]")
    expect(button).to_be_visible()
    frame.locator("//textarea[@id='reason']").fill("ACCESS")
    frame.locator(".btn.btn-primary.btn-submit-request").click()
    page.reload()
    page.locator("a[aria-label='Requests']").click()
    print("Submitted Request...")
    frame.locator(f"(//td[@role='gridcell'][normalize-space()='{domain}.int.inf0.net'])").click()
    frame.locator("//button[@title='Click to retrieve the password']").click()
    close_button = frame.locator(".btn.btn-warning.btn-close-password-screen")
    expect(close_button).to_be_visible()
    print("Retrieving password...")
    pass_text = frame.locator("//input[contains(@class, 'password-')]")
    aws_pwd = pass_text.get_attribute("value")
    host_domain = generate_domain()
    print("Email: " + au_username + host_domain)
    print("Password: " + aws_pwd)
    write_to_file(aws_pwd,domain)

def pass_present(domain: str, page: Page, frame: FrameLocator):
    print("Password already generated...")
    page.reload()
    page.locator("a[aria-label='Requests']").click()
    frame.locator(f"(//td[@role='gridcell'][normalize-space()='{domain}.int.inf0.net'])").click()
    frame.locator("//button[@title='Click to retrieve the password']").click()
    close_button = frame.locator(".btn.btn-warning.btn-close-password-screen")
    expect(close_button).to_be_visible()
    print("Retrieving password...")
    pass_text = frame.locator("//input[contains(@class, 'password-')]")
    aws_pwd = pass_text.get_attribute("value")
    host_domain = generate_domain()
    print("Email: " + au_username + host_domain)
    print("Password: " + aws_pwd)
    
def run(playwright):
    if(domain_choice.lower() == "qarft" or domain_choice.lower() == "dvrft" or domain_choice.lower() == "prrft"):
        start = time.time()
        avail_flag = domain_avail_flag(domain_choice) 
        page = browser_initialisation(playwright)
        open_and_login(page)
        frame = get_frame(page, "#passwordsafeIframe")
        blm_access(frame)
        check = check_availability(f'//*[@id="AccountsGrid"]/div[2]/table/tbody/tr[{avail_flag}]/td[10]/span[2]', frame)
        if check :
            frame.locator(f"//td[normalize-space()='{domain_choice}.int.inf0.net']").click()
            print("Submitting Request...")
            submit_request(domain_choice,frame, page)
        else:
            pass_present(domain_choice, page, frame)
        print('It took {0:0.1f} seconds to retrieve the password.'.format(time.time() - start))    
        proceed_choice()
    else:
        print("Invalid choice, can only be qarft/dvrft/prrft.")
    
with sync_playwright() as playwright: 
    run(playwright)