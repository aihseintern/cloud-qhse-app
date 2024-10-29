from unstructured.partition.pdf import partition_pdf


class Extractor:
    def __init__(self, file_path):
        """
        Initializes the Extractor with a specified PDF file path and partitions
        the PDF into elements using a high-resolution strategy.

        Args:
            file_path (str): The path to the PDF file to be processed.

        Attributes:
            elements (list): A list of partitioned elements from the PDF.
            complete_result (list): A list to store the processed text or HTML from elements.
        """
        self.elements = partition_pdf(
                filename=file_path,
                strategy="hi_res",
                infer_table_structure=True,
                extract_images_in_pdf=False,
                model_name="yolox"
            )
        
        self.complete_result = []
        

    def parse_elements(self):
        """
        Processes the partitioned elements from the PDF and appends the text to
        the complete_result list. The processed text is returned as a single
        string.

        Returns:
            str: The complete text extracted from the PDF.
        """
        for element in self.elements:
            if 'Table' in str(type(element)):
                self.complete_result.append(element.metadata.text_as_html)
                continue

            elif 'Image' in str(type(element)):
                continue

            self.complete_result.append(element.text)

        full_text = '\n'.join(self.complete_result)
        
        return full_text
