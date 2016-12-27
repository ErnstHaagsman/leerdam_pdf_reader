import string

from collections import defaultdict
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

from docx import Document

file = open('/home/eh/Downloads/ld1670.docx', 'rb')
doc = Document(file)

root = doc.element[0]

# collect records
records = []
current_street = ''
for elem in root.iterchildren():
    if isinstance(elem, CT_P):
        captured = Paragraph(elem, root).text.strip()
        if len(captured) == 0:
            continue
        current_street = captured
    elif isinstance(elem, CT_Tbl):
        table = Table(elem,root)
        for row in table.rows:
            record = {
                'street' : current_street,
                'year': row.cells[0].text
            }

            # capture the values from the two cells
            lhs = row.cells[1].text
            rhs = row.cells[2].text

            for name in lhs.split():
                key = name[:-1]
                # The value is up to 30 character of the remaining rhs, up to an enter char
                next_enter = rhs.find('\n')
                if next_enter > 0 and next_enter <= 30:
                    split = next_enter
                elif next_enter > 0:
                    split = 30
                else:
                    split = len(rhs)

                value = rhs[:split]
                rhs = rhs[split + 1:]

                record[key] = value


            records.append(record)

# form CSV of the collected data
headers = {key for key in record.keys() for record in records}

print(','.join(headers))
for record_dict in records:
    record = defaultdict(str, record_dict)
    print(','.join([record[field] for field in headers]))
