from playwright.sync_api import sync_playwright

def run(playwright):
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless = False)
    page = browser.new_page()
    page.goto("https://google.com")
    page.pause()
    
# with sync_playwright() as playwright:
#     run(playwright)