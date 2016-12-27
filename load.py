from __future__ import unicode_literals

import re
import string

from collections import defaultdict

from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, PDFConverter
from pdfminer.layout import LAParams, LTFigure, LTContainer, LTPage
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

MAX_KERNING = 1

class LeerdamConverter(PDFConverter):
    """
    Based on pdfminer.converter.TextConverter
    """

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 showpageno=False, imagewriter=None):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.showpageno = showpageno
        self.imagewriter = imagewriter
        self.street = ''
        self.current_record = None
        self.records = []
        return

    def write_text(self, text):
        self.outfp.write(text.encode(self.codec, 'ignore'))
        return

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTPage):
                for child in item:
                    render(child)
            if isinstance(item, LTFigure):
                self.handle_figure(item)
        render(ltpage)
        return


    def handle_figure(self, ltfigure):
        # Organize chars by line
        lines = {}
        for char in ltfigure:
            if lines.has_key(char.y0):
                lines[char.y0].append(char)
            else:
                lines[char.y0] = [char]

        # Columns:
        #   Year: 71.040
        #   Label: 108.72
        #   Value: 193.848
        for line in [value for (key,value) in sorted(lines.items(), reverse=True)]:
            # See if we have a whole line
            parts = []
            part = line[0].get_text()
            x1 = line[0].x1
            for char in line[1:]:
                if char.x0 - x1 > MAX_KERNING:
                    parts.append(part)
                    part = char.get_text()
                else:
                    part += char.get_text()

                x1 = char.x1

            # Append the last part to the list
            parts.append(part)

            parts = [part.strip() for part in parts if len(part.strip()) > 0]

            if(len(parts) == 1):
                # We have a single line, which could be a street name
                # If it's just a number though, it is a page number
                captured = parts[0].strip()
                if not re.match('/d+', captured):
                    self.street = captured
            elif(len(parts) == 2):
                # We have multiple parts, if we have two, we have a new fact
                record_key = parts[0][:-1]
                record_value = parts[1]
                self.current_record[record_key] = record_value
            elif(len(parts) == 3):
                # If a new record is started, it looks like:
                # 2015      Seller:     Name of Seller

                # New record, so append the current record to the list
                # If this is the first record, `current_record` is None
                if self.current_record is not None:
                    self.records.append(self.current_record)

                self.current_record = {
                    'street': self.street,
                    'year': parts[0]
                }

                # The key is the second captured value, but as it ends in a colon, let's strip that off
                record_key = parts[1][:-1]
                record_value = parts[2]

                self.current_record[record_key] = record_value

    # Some dummy functions to save memory/CPU when all that is wanted
    # is text.  This stops all the image and drawing ouput from being
    # recorded and taking up RAM.
    def render_image(self, name, stream):
        if self.imagewriter is None:
            return
        PDFConverter.render_image(self, name, stream)
        return

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        return

    def save_csv(self, path):
        if self.current_record is not None:
            self.records.append(self.current_record)
            self.current_record = None

        # Format and save CSV
        # form CSV of the collected data
        headers = set()
        for record in self.records:
            for key in record.keys():
                headers.add(key)

        print(','.join(headers))
        for record_dict in self.records:
            record = defaultdict(str, record_dict)
            print(','.join(['"{}"'.format(record[field]) for field in headers]))


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = LeerdamConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    device.save_csv('')

print convert_pdf_to_txt('/home/eh/Downloads/ld1670.pdf')
