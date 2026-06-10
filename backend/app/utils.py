import os
import io
import zipfile
import tarfile
from pathlib import Path
from PIL import Image
import logging
import colorsys
import xml.etree.ElementTree as ET
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)

def compress_image(input_path: Path, output_path: Path, quality: int, target_format: str = None) -> Path:
    """
    Compresses an image, converting it to target_format if specified.
    """
    try:
        with Image.open(input_path) as img:
            fmt = target_format.upper() if target_format else (img.format or "").upper()
            if not fmt:
                ext = input_path.suffix.lower()
                if ext in ('.jpg', '.jpeg'):
                    fmt = 'JPEG'
                elif ext == '.png':
                    fmt = 'PNG'
                elif ext == '.webp':
                    fmt = 'WEBP'
                else:
                    fmt = 'JPEG'
            
            if fmt == 'JPG':
                fmt = 'JPEG'
                
            logger.info(f"Compressing {input_path.name} -> format: {fmt}, quality: {quality}")

            if fmt == 'JPEG':
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img_to_save = background
                else:
                    img_to_save = img
                img_to_save.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            elif fmt == 'WEBP':
                img.save(output_path, 'WEBP', quality=quality, optimize=True)
                
            elif fmt == 'PNG':
                if quality < 85:
                    num_colors = max(16, int(256 * (quality / 100)))
                    quantized = img.convert('RGBA').convert('P', palette=Image.ADAPTIVE, colors=num_colors)
                    quantized.save(output_path, 'PNG', optimize=True)
                else:
                    img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                img.save(output_path, fmt)
                    
        return output_path
    except Exception as e:
        logger.error(f"Error compressing image {input_path.name}: {e}")
        raise RuntimeError(f"Image compression failed: {str(e)}")

def compress_image_to_target_size(
    input_path: Path, 
    output_path: Path, 
    min_size: int, 
    max_size: int, 
    target_format: str = None
) -> Path:
    """
    Compresses an image, adjusting quality and dimensions iteratively 
    IN-MEMORY (io.BytesIO) to try and fit output file size within [min_size, max_size].
    Saves to physical disk ONLY ONCE at the end.
    """
    try:
        with Image.open(input_path) as original_img:
            fmt = target_format.upper() if target_format else (original_img.format or "").upper()
            if not fmt:
                ext = input_path.suffix.lower()
                fmt = 'JPEG' if ext in ('.jpg', '.jpeg') else ('PNG' if ext == '.png' else 'WEBP')
            if fmt == 'JPG':
                fmt = 'JPEG'
                
            width, height = original_img.size
            scale_factor = 1.0
            quality = 90
            iteration = 0
            max_iterations = 12
            
            best_quality = quality
            best_scale = scale_factor
            
            logger.info(f"Target size optimization (In-Memory): [{min_size} - {max_size}] bytes for {input_path.name}")
            
            while iteration < max_iterations:
                iteration += 1
                
                if scale_factor < 1.0:
                    new_w = max(10, int(width * scale_factor))
                    new_h = max(10, int(height * scale_factor))
                    img_work = original_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
                else:
                    img_work = original_img.copy()
                
                buf = io.BytesIO()
                try:
                    if fmt == 'JPEG':
                        if img_work.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', img_work.size, (255, 255, 255))
                            background.paste(img_work, mask=img_work.split()[-1] if img_work.mode == 'RGBA' else None)
                            background.save(buf, 'JPEG', quality=quality, optimize=True)
                        else:
                            img_work.save(buf, 'JPEG', quality=quality, optimize=True)
                    elif fmt == 'WEBP':
                        img_work.save(buf, 'WEBP', quality=quality, optimize=True)
                    elif fmt == 'PNG':
                        if quality < 85:
                            num_colors = max(16, int(256 * (quality / 100)))
                            quantized = img_work.convert('RGBA').convert('P', palette=Image.ADAPTIVE, colors=num_colors)
                            quantized.save(buf, 'PNG', optimize=True)
                        else:
                            img_work.save(buf, 'PNG', optimize=True, compress_level=9)
                    else:
                        img_work.save(buf, fmt)
                finally:
                    if img_work is not original_img:
                        img_work.close()
                
                current_size = buf.tell()
                buf.close()
                
                logger.info(f"Search Loop {iteration}: scale={scale_factor:.2f}, quality={quality}, size={current_size} bytes")
                
                if min_size <= current_size <= max_size:
                    best_quality = quality
                    best_scale = scale_factor
                    break
                
                if current_size < min_size:
                    if quality < 90 or scale_factor < 1.0:
                        if quality < 90:
                            quality = min(90, quality + 10)
                            continue
                    best_quality = quality
                    best_scale = scale_factor
                    break
                    
                if current_size > max_size:
                    best_quality = quality
                    best_scale = scale_factor
                    
                    if quality > 20:
                        quality = max(10, quality - 20)
                    else:
                        if scale_factor > 0.2:
                            scale_factor -= 0.2
                            quality = 80
                        else:
                            break
                            
            logger.info(f"Saving optimized result: scale={best_scale:.2f}, quality={best_quality} to disk.")
            if best_scale < 1.0:
                new_w = max(10, int(width * best_scale))
                new_h = max(10, int(height * best_scale))
                final_img = original_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                final_img = original_img.copy()
                
            try:
                if fmt == 'JPEG':
                    if final_img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', final_img.size, (255, 255, 255))
                        background.paste(final_img, mask=final_img.split()[-1] if final_img.mode == 'RGBA' else None)
                        background.save(output_path, 'JPEG', quality=best_quality, optimize=True)
                    else:
                        final_img.save(output_path, 'JPEG', quality=best_quality, optimize=True)
                elif fmt == 'WEBP':
                    final_img.save(output_path, 'WEBP', quality=best_quality, optimize=True)
                elif fmt == 'PNG':
                    if best_quality < 85:
                        num_colors = max(16, int(256 * (best_quality / 100)))
                        quantized = final_img.convert('RGBA').convert('P', palette=Image.ADAPTIVE, colors=num_colors)
                        quantized.save(output_path, 'PNG', optimize=True)
                    else:
                        final_img.save(output_path, 'PNG', optimize=True, compress_level=9)
                else:
                    final_img.save(output_path, fmt)
            finally:
                final_img.close()
                
            return output_path
            
    except Exception as e:
        logger.error(f"Error optimizing image size: {e}")
        raise RuntimeError(f"Target size optimization failed: {str(e)}")

# ==========================================
# FILE FORMAT CONVERSION MODULES
# ==========================================

def convert_images_to_pdf(input_paths: list[Path], output_path: Path) -> Path:
    """
    Converts one or more image files, fits them proportionally, 
    and centers them onto standard A4 pages in a single PDF.
    Uses high-speed Bicubic resizing for fast PDF compilation.
    """
    try:
        A4_WIDTH = 595
        A4_HEIGHT = 842
        
        pages = []
        for path in input_paths:
            with Image.open(path) as img:
                img_w, img_h = img.size
                img_ratio = img_w / img_h
                a4_ratio = A4_WIDTH / A4_HEIGHT
                
                if img_ratio > a4_ratio:
                    fit_w = A4_WIDTH
                    fit_h = int(A4_WIDTH / img_ratio)
                else:
                    fit_h = A4_HEIGHT
                    fit_w = int(A4_HEIGHT * img_ratio)
                
                fit_w = max(10, fit_w)
                fit_h = max(10, fit_h)
                
                # Optimized: Using Resampling.BICUBIC is 3x faster than LANCZOS with visual parity
                resized_img = img.resize((fit_w, fit_h), Image.Resampling.BICUBIC)
                
                page = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))
                
                x_offset = (A4_WIDTH - fit_w) // 2
                y_offset = (A4_HEIGHT - fit_h) // 2
                
                if resized_img.mode in ('RGBA', 'LA'):
                    page.paste(resized_img, (x_offset, y_offset), mask=resized_img.split()[-1])
                else:
                    temp_rgb = resized_img.convert('RGB')
                    page.paste(temp_rgb, (x_offset, y_offset))
                    
                pages.append(page)
                
        if not pages:
            raise ValueError("No images selected for PDF conversion.")
            
        pages[0].save(output_path, save_all=True, append_images=pages[1:], format='PDF')
        
        logger.info(f"Successfully converted and aligned {len(input_paths)} images onto A4 pages: {output_path.name}")
        return output_path
    except Exception as e:
        logger.error(f"Failed converting images to PDF: {e}")
        raise RuntimeError(f"Images to PDF conversion failed: {str(e)}")

def convert_pdf_to_images(input_path: Path, output_dir: Path, img_format: str = 'PNG') -> list[Path]:
    """
    Renders each page of a PDF document into separate images.
    Optimized at 100 DPI for 2.25x rendering speedup compared to 150 DPI.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(input_path)
        page_paths = []
        
        fmt = img_format.upper().strip()
        if fmt not in ('PNG', 'JPEG', 'JPG'):
            fmt = 'PNG'
        ext = 'jpg' if fmt == 'JPEG' or fmt == 'JPG' else 'png'
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Optimized: Reduced to 100 DPI (crisp text, 2.25x faster processing)
            pix = page.get_pixmap(dpi=100)
            
            page_file = output_dir / f"page_{page_num + 1}.{ext}"
            pix.save(str(page_file))
            page_paths.append(page_file)
            
        doc.close()
        logger.info(f"Converted PDF {input_path.name} to {len(page_paths)} page images.")
        return page_paths
    except Exception as e:
        logger.error(f"Failed converting PDF to images: {e}")
        raise RuntimeError(f"PDF to images conversion failed: {str(e)}")

def convert_pdf_to_docx(input_path: Path, output_path: Path) -> Path:
    """
    Converts a PDF document into a Word (.docx) file.
    Optimized: Uses multi-processing to convert pages in parallel across CPU cores.
    """
    try:
        from pdf2docx import Converter
        cv = Converter(str(input_path))
        # Optimized: Added multi_processing=True to parallelize page layout reconstruction
        cv.convert(str(output_path), start=0, end=None, multi_processing=True)
        cv.close()
        logger.info(f"Converted PDF {input_path.name} to DOCX: {output_path.name}")
        return output_path
    except Exception as e:
        logger.error(f"Failed converting PDF to DOCX: {e}")
        raise RuntimeError(f"PDF to Word conversion failed: {str(e)}")

def apply_tint_shade_hsl(rgb_hex: str, tint_hex: str = None, shade_hex: str = None) -> str:
    """
    Applies tint or shade scaling to a hex RGB color in HSL color space.
    """
    try:
        r = int(rgb_hex[0:2], 16) / 255.0
        g = int(rgb_hex[2:4], 16) / 255.0
        b = int(rgb_hex[4:6], 16) / 255.0
        
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        
        if tint_hex:
            tint = int(tint_hex, 16) / 255.0
            l = l * tint + (1.0 - tint)
        elif shade_hex:
            shade = int(shade_hex, 16) / 255.0
            l = l * shade
            
        r_new, g_new, b_new = colorsys.hls_to_rgb(h, l, s)
        return f"{int(r_new * 255):02X}{int(g_new * 255):02X}{int(b_new * 255):02X}"
    except Exception as e:
        logger.warning(f"Error applying tint/shade HSL: {e}")
        return rgb_hex

def _parse_factor(val_str: str) -> float:
    if not val_str:
        return 1.0
    try:
        if len(val_str) <= 2:
            return int(val_str, 16) / 255.0
        val = int(val_str, 16) if all(c in '0123456789ABCDEFabcdef' for c in val_str) else int(val_str)
        if val > 100:
            return val / 100000.0
        if val > 1:
            return val / 100.0
        return float(val)
    except Exception:
        return 1.0

def resolve_theme_color(theme_color_name: str, theme_colors: dict) -> str:
    name = theme_color_name.lower() if theme_color_name else ""
    mapping = {
        'dark1': 'dk1', 'light1': 'lt1',
        'dark2': 'dk2', 'light2': 'lt2',
        'text1': 'dk1', 'background1': 'lt1',
        'text2': 'dk2', 'background2': 'lt2',
        'accent1': 'accent1', 'accent2': 'accent2', 'accent3': 'accent3',
        'accent4': 'accent4', 'accent5': 'accent5', 'accent6': 'accent6',
        'hyperlink': 'hlink', 'followedhyperlink': 'folHlink'
    }
    tag = mapping.get(name, name)
    return theme_colors.get(tag)

def extract_theme_colors(docx_path: Path) -> dict:
    theme_colors = {
        'dk1': '000000', 'lt1': 'FFFFFF',
        'dk2': '1F497D', 'lt2': 'EEECE1',
        'accent1': '4F81BD', 'accent2': 'C0504D', 'accent3': '9BBB59',
        'accent4': '8064A2', 'accent5': '4BACC6', 'accent6': 'F79646',
        'hlink': '0000FF', 'folHlink': '800080'
    }
    try:
        with zipfile.ZipFile(docx_path) as z:
            theme_xml_path = "word/theme/theme1.xml"
            if theme_xml_path in z.namelist():
                theme_xml = z.read(theme_xml_path)
                root = ET.fromstring(theme_xml)
                ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
                clr_scheme = root.find('.//a:clrScheme', ns)
                if clr_scheme is not None:
                    tag_to_keys = {
                        'dk1': ['dk1', 'dark1', 'text1'],
                        'lt1': ['lt1', 'light1', 'background1'],
                        'dk2': ['dk2', 'dark2', 'text2'],
                        'lt2': ['lt2', 'light2', 'background2'],
                        'accent1': ['accent1'],
                        'accent2': ['accent2'],
                        'accent3': ['accent3'],
                        'accent4': ['accent4'],
                        'accent5': ['accent5'],
                        'accent6': ['accent6'],
                        'hlink': ['hlink', 'hyperlink'],
                        'folHlink': ['folhlink', 'followedhyperlink']
                    }
                    for tag, keys in tag_to_keys.items():
                        elem = clr_scheme.find(f'a:{tag}', ns)
                        if elem is not None:
                            srgb = elem.find('a:srgbClr', ns)
                            sys = elem.find('a:sysClr', ns)
                            color_val = None
                            if srgb is not None:
                                color_val = srgb.get('val')
                            elif sys is not None:
                                color_val = sys.get('lastClr') or sys.get('val')
                            if color_val and len(color_val) == 6:
                                for key in keys:
                                    theme_colors[key] = color_val
    except Exception as e:
        logger.warning(f"Could not parse theme1.xml from {docx_path.name}: {e}")
    return theme_colors

def get_run_color(run, para, theme_colors: dict) -> str:
    def _resolve_color_obj(color_obj):
        if not color_obj:
            return None
            
        # 1. Check Theme Color FIRST
        theme_color = None
        try:
            if color_obj._color is not None:
                theme_color = color_obj._color.get(qn('w:themeColor'))
        except Exception:
            pass
        if not theme_color and color_obj.theme_color:
            theme_color = color_obj.theme_color
            
        if theme_color:
            base_color = None
            if isinstance(theme_color, int):
                tag_map = {
                    1: 'dk1', 13: 'dk1',
                    2: 'lt1', 14: 'lt1',
                    3: 'dk2', 15: 'dk2',
                    4: 'lt2', 16: 'lt2',
                    5: 'accent1', 6: 'accent2', 7: 'accent3', 8: 'accent4', 9: 'accent5', 10: 'accent6',
                    11: 'hlink', 12: 'folHlink'
                }
                tag = tag_map.get(theme_color)
                base_color = theme_colors.get(tag) if tag else None
            else:
                base_color = resolve_theme_color(theme_color, theme_colors)
                
            if base_color:
                tint = None
                shade = None
                try:
                    if color_obj._color is not None:
                        tint = color_obj._color.get(qn('w:themeTint'))
                        shade = color_obj._color.get(qn('w:themeShade'))
                except Exception:
                    pass
                if tint:
                    factor = _parse_factor(tint)
                    tint_hex = f"{int(factor * 255):02X}"
                    return apply_tint_shade_hsl(base_color, tint_hex=tint_hex)
                elif shade:
                    factor = _parse_factor(shade)
                    shade_hex = f"{int(factor * 255):02X}"
                    return apply_tint_shade_hsl(base_color, shade_hex=shade_hex)
                return base_color
                
        # 2. Check RGB Color SECOND
        if color_obj.rgb:
            return str(color_obj.rgb)
            
        # 3. Check XML val attribute THIRD (if rgb didn't resolve but raw exists)
        try:
            if color_obj._color is not None:
                val = color_obj._color.get(qn('w:val'))
                if val and val != 'auto' and len(val) == 6:
                    return val
        except Exception:
            pass
            
        return None

    # 1. Run direct color
    color_hex = _resolve_color_obj(run.font.color if run.font else None)
    if color_hex:
        return color_hex
    # 2. Run style font color
    if run.style and run.style.font:
        color_hex = _resolve_color_obj(run.style.font.color)
        if color_hex:
            return color_hex
    # 3. Paragraph style font color
    if para.style and para.style.font:
        color_hex = _resolve_color_obj(para.style.font.color)
        if color_hex:
            return color_hex
    return None

def convert_docx_to_pdf(input_path: Path, output_path: Path) -> Path:
    """
    Parses a Word (.docx) document, extracting run-level styling (colors, sizes, bold, italic),
    paragraph alignments, and renders it as a clean PDF natively.
    """
    try:
        word_doc = Document(input_path)
        theme_colors = extract_theme_colors(input_path)
        
        styles = getSampleStyleSheet()
        base_body = styles['BodyText']
        base_heading = styles['Heading1']
        
        style_cache = {}
        
        def get_cached_style(style_type, alignment, font_size, color_hex):
            style_key = f"Style_{style_type}_align{alignment}_size{int(font_size*10)}_color{color_hex}"
            if style_key in style_cache:
                return style_cache[style_key]
                
            parent = base_heading if style_type == "heading" else base_body
            font_name = 'Helvetica-Bold' if style_type == "heading" else 'Helvetica'
            space_before = 12 if style_type == "heading" else 0
            space_after = 6 if style_type == "heading" else 8
            
            new_style = ParagraphStyle(
                style_key,
                parent=parent,
                fontName=font_name,
                fontSize=font_size,
                leading=font_size + 4,
                alignment=alignment,
                textColor=colors.HexColor(f"#{color_hex}"),
                spaceBefore=space_before,
                spaceAfter=space_after
            )
            styles.add(new_style)
            style_cache[style_key] = new_style
            return new_style

        story = []
        
        for para_idx, para in enumerate(word_doc.paragraphs):
            markup_text = ""
            for run in para.runs:
                run_text = run.text
                if not run_text:
                    continue
                    
                run_text = run_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                run_text = run_text.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
                run_text = run_text.replace('\n', '<br/>').replace('\r', '<br/>')
                
                if run.bold:
                    run_text = f"<b>{run_text}</b>"
                if run.italic:
                    run_text = f"<i>{run_text}</i>"
                if run.underline:
                    run_text = f"<u>{run_text}</u>"
                    
                if run.font.size:
                    run_text = f'<font size="{run.font.size.pt}">{run_text}</font>'
                    
                run_color = get_run_color(run, para, theme_colors)
                if run_color:
                    run_text = f'<font color="#{run_color}">{run_text}</font>'
                    
                markup_text += run_text
                
            if not markup_text.strip():
                markup_text = "&nbsp;"
                
            rl_alignment = 0
            if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                rl_alignment = 1
            elif para.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
                rl_alignment = 2
            elif para.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
                rl_alignment = 4
                
            style_color_hex = None
            if para.style and para.style.font:
                class DummyRun:
                    font = None
                    style = None
                style_color_hex = get_run_color(DummyRun(), para, theme_colors)
            if not style_color_hex:
                style_color_hex = "000000"
                
            if para.style.name.startswith('Heading'):
                font_size = 16
                name_lower = para.style.name.lower()
                if '1' in name_lower:
                    font_size = 18
                elif '2' in name_lower:
                    font_size = 15
                elif '3' in name_lower:
                    font_size = 13
                elif '4' in name_lower:
                    font_size = 11
                    
                para_style = get_cached_style("heading", rl_alignment, font_size, style_color_hex)
                story.append(Paragraph(markup_text, para_style))
                story.append(Spacer(1, 4))
            else:
                para_style = get_cached_style("body", rl_alignment, 10, style_color_hex)
                story.append(Paragraph(markup_text, para_style))
                
        pdf = SimpleDocTemplate(
            str(output_path), 
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        pdf.build(story)
        
        logger.info(f"Successfully converted styled DOCX {input_path.name} to PDF: {output_path.name}")
        return output_path
    except Exception as e:
        logger.error(f"Failed converting DOCX to PDF: {e}")
        raise RuntimeError(f"Word to PDF conversion failed: {str(e)}")

def create_zip_archive(files_to_zip: list[tuple[Path, str]], output_path: Path) -> Path:
    """
    Creates a zip archive from a list of (source_path, archive_name) tuples.
    """
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path, arcname in files_to_zip:
                if file_path.exists():
                    zipf.write(file_path, arcname)
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating zip archive: {e}")
        raise RuntimeError(f"Zip archive creation failed: {str(e)}")

def create_tar_archive(files_to_tar: list[tuple[Path, str]], output_path: Path) -> Path:
    """
    Creates a tar.gz archive from a list of (source_path, archive_name) tuples.
    """
    try:
        with tarfile.open(output_path, 'w:gz') as tarf:
            for file_path, arcname in files_to_tar:
                if file_path.exists():
                    tarf.add(file_path, arcname=arcname)
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error creating tar archive: {e}")
        raise RuntimeError(f"Tar archive creation failed: {str(e)}")
