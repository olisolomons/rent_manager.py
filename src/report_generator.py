from pathlib import Path
from typing import Sequence

from fpdf import FPDF, HTMLMixin

from rent_manager.state.rent_manager_state import RentManagerState, RentCalculations


class PDF(FPDF, HTMLMixin):
    pass


def hello_world():
    gen = PDFGenerator()
    data = [[str(i), f'{i**2=}', ' ' + 'a' * i] for i in range(5)]
    gen.put_table(['Head 1', 'Head 2', 'Head 3'], data)
    gen.output('hello_world.pdf')


class PDFGenerator:
    def __init__(self):
        self.pdf = PDF()
        self.pdf.add_page()
        self.pdf.set_font('helvetica', size=12)

        self.html_buffer = []

    def put(self, html_fragment):
        self.html_buffer.append(html_fragment)

    def tag(self, tag_name: str, **attributes: str):
        return AutoClosingTag(self, tag_name, **attributes)

    def put_table(self, headers: Sequence[str | tuple[str, float]], data):
        with self.tag('table', border='1'):
            with self.tag('thead'):
                with self.tag('tr'):
                    def get_weight(header):
                        return 1 if isinstance(header, str) else header[1]

                    total_weight = sum(get_weight(header) for header in headers)
                    widths = [int(get_weight(header) / total_weight * 100) for header in headers]
                    shortfall = 100 - sum(widths)
                    for i in range(shortfall):
                        widths[i] += 1

                    for header, width in zip(headers, widths):
                        with self.tag('th', width=f'{width}%'):
                            if isinstance(header, str):
                                self.put(header)
                            else:
                                self.put(header[0])
            with self.tag('tbody'):
                for row in data:
                    with self.tag('tr'):
                        for cell in row:
                            with self.tag('td'):
                                self.put(cell)

    def output(self, path):
        self.pdf.write_html(''.join(self.html_buffer))
        self.pdf.output(path)


class AutoClosingTag:
    def __init__(self, report_generator: PDFGenerator, tag_name: str, **attributes: str):
        self.report_generator = report_generator
        self.tag_name = tag_name
        self.attributes = attributes

    def __enter__(self):
        attributes_string = ''.join(f' {key}="{value}"' for key, value in self.attributes.items())
        self.report_generator.put(f'<{self.tag_name}{attributes_string}>')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.report_generator.put(f'</{self.tag_name}>')


def format_currency(amount, symbol='£'):
    return f'{symbol}{amount / 100:.2f}'


def generate_report(data: RentManagerState, calculations: RentCalculations, export_path: str | Path):
    pdf = PDFGenerator()
    rent_for_months = []
    for month, paid in calculations.rent_for_months:
        month_arrears = data.rent_arrangement_data.monthly_rent - paid
        if month_arrears == 0:
            color = '00AA00'
        elif month_arrears > 0:
            color = 'DAD000'
        else:
            color = 'AA0000'
        rent_for_months.append([
            month.strftime('%b %Y'), format_currency(paid),
            f'<font color="#{color}">' + format_currency(month_arrears) + '</font>'
        ])
    pdf.put_table(
        ['Month', 'Amount Paid', 'Arrears for month'],
        rent_for_months
    )
    pdf.output(str(export_path))


if __name__ == '__main__':
    hello_world()
