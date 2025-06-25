from charleston_agent import save_property_card_pdf, save_deed_pdf

if __name__ == "__main__":
    test_tms = "5590200072"
    output_folder = f"./output/Charleston/{test_tms}"
    
    print("Starting to save property card PDF...")
    book_page_pairs = save_property_card_pdf(test_tms, output_folder)
    
    print("Starting to save deed PDFs...")
    for book, page_num in book_page_pairs:
        save_deed_pdf(book, page_num, output_folder)
    
    print("All done.")
