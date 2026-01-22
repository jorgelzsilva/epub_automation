import zipfile
import os
import shutil

def extract_epub(epub_path, extract_to):
    """
    Extracts an ePub file to a directory.
    Returns the path to the OPF file and the content directory (directory containing OPF).
    """
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    # Find OPF file
    opf_path = None
    for root, dirs, files in os.walk(extract_to):
        for file in files:
            if file.endswith('.opf'):
                opf_path = os.path.join(root, file)
                break
        if opf_path:
            break
            
    if not opf_path:
        raise FileNotFoundError("OPF file not found in the ePub.")
        
    return opf_path, os.path.dirname(opf_path)

def package_epub(source_dir, output_path):
    """
    Zips a directory into an ePub file.
    Critically, mimetype must be the first file and uncompressed.
    """
    mimetype_path = os.path.join(source_dir, 'mimetype')
    if not os.path.exists(mimetype_path):
        # Create mimetype if missing (rare case)
        with open(mimetype_path, 'w') as f:
            f.write('application/epub+zip')

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
        # Add mimetype first (STORED / No Compression)
        zip_out.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
        
        # Add everything else
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == 'mimetype':
                    continue
                file_path = os.path.join(root, file)
                archive_name = os.path.relpath(file_path, source_dir)
                zip_out.write(file_path, archive_name)
