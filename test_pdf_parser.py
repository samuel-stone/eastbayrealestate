import pdfplumber

def test_raw_text(file_path):
    print(f"Opening {file_path}...")
    try:
        with pdfplumber.open(file_path) as pdf:
            # Grab just the first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            print("\n=== RAW TEXT (FIRST 25 LINES) ===")
            # Split the text by line breaks and print the first 25
            for line in text.split('\n')[:25]:
                print(line)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_raw_text("permit_report.pdf")
