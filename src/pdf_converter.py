from pdf2image import convert_from_path

def pdf_to_images(pdf_path, poppler_path):
    return convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=poppler_path
    )