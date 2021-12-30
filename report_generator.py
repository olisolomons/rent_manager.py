from fpdf import FPDF, HTMLMixin


class PDF(FPDF, HTMLMixin):
    pass


def hello_world():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('helvetica', size=12)
    pdf.write_html("""
      <p>Hello world</p>
    """)
    pdf.output("hello_world.pdf")


if __name__ == '__main__':
    hello_world()
