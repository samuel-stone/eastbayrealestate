from scraper.discover_listings import main as discover_main

if __name__ == "__main__":
    print("[*] Triggering fresh listing discovery batch...")
    discover_main()
    print("[+] Discovery batch finished.")
