import io
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

pdf = SimpleDocTemplate(io.BytesIO())
styles = getSampleStyleSheet()

# Try hex color in font tag
story = [Paragraph('Hello <font color="#123456">Hex Color</font> Test', styles['Normal'])]
try:
    pdf.build(story)
    print("Hex color #123456: SUCCESS")
except Exception as e:
    print("Hex color #123456: ERROR:", e)

# Try font color without '#'
story2 = [Paragraph('Hello <font color="123456">No Hash Color</font> Test', styles['Normal'])]
try:
    pdf.build(story2)
    print("Color 123456 (no hash): SUCCESS")
except Exception as e:
    print("Color 123456 (no hash): ERROR:", e)

# Try standard colors
story3 = [Paragraph('Hello <font color="red">Red Color</font> Test', styles['Normal'])]
try:
    pdf.build(story3)
    print("Color red: SUCCESS")
except Exception as e:
    print("Color red: ERROR:", e)
