from mistralai import Mistral
import os
from pathlib import Path
import base64


def process_pdf_to_markdown(pdf_path: str, output_path: str = None) -> str:
    """
    Process a PDF file using Mistral's OCR and save the output as markdown.

    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Path to save the markdown output.
                                   If None, will use PDF name with .md extension

    Returns:
        str: Path to the saved markdown file
    """
    # Get API key from environment
    api_key = "3DzeqFDNpWcWtOvK8LtoYUOAYXJUGoqi"
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable not set")

    # Initialize Mistral client
    client = Mistral(api_key=api_key)

    # Upload the PDF file
    with open(pdf_path, "rb") as pdf_file:
        uploaded_pdf = client.files.upload(
            file={
                "file_name": Path(pdf_path).name,
                "content": pdf_file,
            },
            purpose="ocr",
        )

    # Get signed URL for the uploaded file
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    # Process the document with OCR
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True,
    )

    # If no output path specified, create one based on input filename
    if output_path is None:
        output_path = str(Path(pdf_path).with_suffix(".md"))

    # Create output directory for images if it doesn't exist
    image_dir = Path(output_path).parent / "images"
    image_dir.mkdir(exist_ok=True)

    # Process and save the OCR response
    markdown_content = ""

    # Process each page in the response
    for page in ocr_response.pages:
        # Add page markdown content
        markdown_content += page.markdown + "\n\n"
        # Process any images in the page
        if hasattr(page, "images") and page.images:
            for image in page.images:
                if hasattr(image, "image_base64") and image.image_base64:
                    # Save image to file
                    try:
                        # Check if the base64 string has a prefix and remove it
                        if "," in image.image_base64:
                            # Handle data URI format (e.g., "data:image/jpeg;base64,...")
                            _, image_data_string = image.image_base64.split(",", 1)
                        else:
                            image_data_string = image.image_base64

                        image_data = base64.b64decode(image_data_string)

                        # Add correct file extension based on content type if available
                        image_ext = ".png"  # Default extension
                        if ";" in image.image_base64 and "data:" in image.image_base64:
                            content_type = image.image_base64.split(";")[0].split(":")[
                                1
                            ]
                            if "jpeg" in content_type or "jpg" in content_type:
                                image_ext = ".jpg"
                            elif "png" in content_type:
                                image_ext = ".png"
                            elif "gif" in content_type:
                                image_ext = ".gif"

                        # Save with appropriate extension
                        image_path = image_dir / f"{image.id}{image_ext}"

                        with open(image_path, "wb") as f:
                            f.write(image_data)
                    except Exception as e:
                        print(f"Error saving image {image.id}: {e}")

    # Save the combined markdown content
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return output_path


if __name__ == "__main__":
    pdf_path = "splitted.pdf"
    output_file = process_pdf_to_markdown(pdf_path)
    print(f"PDF processed and saved to: {output_file}")
