from charleston_agent import save_property_card_pdf

if __name__ == "__main__":
    # Example TMS number to test
    test_tms = "5590200072"
    output_folder = f"./output/Charleston/{test_tms}"
    
    print("Starting to save property card PDF...")
    save_property_card_pdf(test_tms, output_folder)
    print("Done.")
