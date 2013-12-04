from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import BaseDocTemplate, Paragraph, Image
from reportlab.platypus import Table, TableStyle, flowables
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import FrameBreak, PageTemplate, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.barcode import code128


class FillFrame(Frame):
    def drawBoundary(self, c):
        """
        Draw the rectangles for the header and footer
        This is just for looks
        """
        c.setStrokeColorRGB(.8, .8, .8)
        c.setFillColorRGB(.8, .8, .8)
        c.rect(.125*inch, 7.5*inch, 10.75*inch, .875*inch, fill=1)
        c.rect(.125*inch, .125*inch, 10.75*inch, .825*inch, fill=1)
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(1, 1, 1)
        c.rect(8*inch, 7.625*inch, 2.5*inch, .625*inch, fill=1)
        c.rect(.25*inch, .25*inch, 2.5*inch, .625*inch, fill=1)
        c.setFillColorRGB(0, 0, 0)


class FillFrameHot(Frame):
    def drawBoundary(self, c):
        """
        Draw the rectangles for the header and footer
        This is just for looks
        """
        c.setStrokeColorRGB(.4, .4, .4)
        c.setFillColorRGB(.4, .4, .4)
        c.rect(.125*inch, 7.5*inch, 10.75*inch, .875*inch, fill=1)
        c.rect(.125*inch, .125*inch, 10.75*inch, .825*inch, fill=1)
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(1, 1, 1)
        c.rect(8*inch, 7.625*inch, 2.5*inch, .625*inch, fill=1)
        c.rect(.25*inch, .25*inch, 2.5*inch, .625*inch, fill=1)
        c.setFillColorRGB(0, 0, 0)


class WorkOrder():
    Title = "Work Order Prints"
    Author = "Ryan Hanson"

    def __init__(self):
        self.frame_fill = FillFrame(x1=.0*inch, y1=0*inch, width=0*inch, height=0*inch, showBoundary=1)
        self.frame_fill_hot = FillFrameHot(x1=.0*inch, y1=0*inch, width=0*inch, height=0*inch, showBoundary=1)
        self.frame_header = Frame(x1=.25*inch, y1=7.75*inch, width=8*inch, height=.5*inch)
        self.frame_barcode_top = Frame(x1=8*inch, y1=7.375*inch, width=2.5*inch, height=.875*inch)
        self.frame1 = Frame(x1=.25*inch, y1=1*inch, width=2.25*inch, height=6.5*inch)
        self.frame2 = Frame(x1=2.5*inch, y1=1*inch, width=8.5*inch, height=6.5*inch)
        self.frame_footer = Frame(x1=0*inch, y1=0*inch, width=11*inch, height=1*inch)
        self.frame_barcode_bottom = Frame(x1=.25*inch, y1=0*inch, width=2.5*inch, height=.875*inch)
        self.main_page = PageTemplate(frames=[self.frame_fill, self.frame_header, self.frame_barcode_top, self.frame1,
                                              self.frame2, self.frame_footer, self.frame_barcode_bottom], id="main")
        self.hot_page = PageTemplate(frames=[self.frame_fill_hot, self.frame_header, self.frame_barcode_top,
                                             self.frame1, self.frame2, self.frame_footer,
                                             self.frame_barcode_bottom], id="hot")

        self.doc = BaseDocTemplate('indWo.pdf', pagesize=landscape(letter), leftMargin=72, title=self.Title,
                                   author=self.Author, showBoundary=0)

        self.styles = getSampleStyleSheet()
        self.style_n = self.styles["BodyText"]
        self.style_n.alignment = TA_CENTER
        self.style_bh = self.styles["Normal"]
        self.style_bh.alignment = TA_LEFT
        self.story = []

    def add_page(self, h_data, rows, row_data, print_loc):
        #set up header table
        h_job = Paragraph(" Job #:", self.style_bh)
        h_machine = Paragraph(" Machine:", self.style_bh)
        h_date_ = Paragraph(" Date:", self.style_bh)
        job = Paragraph(unicode(h_data[0]), self.style_bh)
        machine = Paragraph(unicode(h_data[2]), self.style_bh)
        date_ = Paragraph(unicode(h_data[1]), self.style_bh)
        header = [[h_job, job, h_date_, date_, h_machine, machine]]
        heading = Table(header, colWidths=[1*inch, 1.5*inch, 1*inch,
                                           1.5*inch, 1*inch, 1.5*inch])
        heading.hAlign = 'LEFT'
        heading.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                     ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                     ('BACKGROUND', (1, 0), (1, 0), colors.white),
                                     ('BACKGROUND', (3, 0), (3, 0), colors.white),
                                     ('BACKGROUND', (5, 0), (5, 0), colors.white)]))

        hot = row_data[0].value(8).toString()
        if hot == "0":
            self.doc.addPageTemplates([self.main_page, self.hot_page])
        else:
            self.doc.addPageTemplates([self.hot_page, self.main_page])
        for q in range(rows):
            self.story.append(FrameBreak())
            self.story.append(heading)
            self.story.append(FrameBreak())
            tracking = unicode(row_data[q].value(10).toString())
            code = code128.Code128(tracking, barWidth=1.25)
            code.hAlign = 'CENTER'
            self.story.append(code)
            text_code = Paragraph(tracking, self.style_n)
            self.story.append(text_code)
            self.story.append(FrameBreak())

            #Part data
            h_part_num = Paragraph('''<b>Part #:</b>''', self.style_bh)
            h_qty = Paragraph('''<b>Qty:</b>''', self.style_bh)
            h_description = Paragraph('''<b>Description:</b>''', self.style_bh)
            h_mat = Paragraph('''<b>Material:</b>''', self.style_bh)
            h_routing = Paragraph('''<b>Routing:</b>''', self.style_bh)
            h_destination = Paragraph('''<b>Destination:</b>''', self.style_bh)
            h_notes = Paragraph('''<b>Notes:</b>''', self.style_bh)
            h_order = Paragraph('''<b>Order:</b>''', self.style_bh)
            part_num = Paragraph(unicode(row_data[q].value(0).toString()), self.style_bh)
            qty = Paragraph(unicode(row_data[q].value(1).toString()), self.style_bh)
            description = Paragraph(unicode(row_data[q].value(2).toString()), self.style_bh)
            mat = Paragraph(unicode(row_data[q].value(3).toString()), self.style_bh)
            routing = Paragraph(unicode(row_data[q].value(4).toString()), self.style_bh)
            destination = Paragraph(unicode(row_data[q].value(5).toString()), self.style_bh)
            notes = Paragraph(unicode(row_data[q].value(6).toString()), self.style_bh)
            order = Paragraph(unicode(row_data[q].value(9).toString()), self.style_bh)
            prints = unicode(row_data[q].value(7).toString())

            data = [[h_part_num, part_num], [h_qty, qty], [h_description, description], [h_mat, mat],
                   [h_routing, routing], [h_destination, destination], [h_notes, notes], [h_order, order]]
            table = Table(data, colWidths=[1*inch, 1.375*inch])
            table.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                       ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))
            self.story.append(table)
            self.story.append(FrameBreak())

            if prints != "":
                prints = "{0}/{1}.jpg".format(print_loc, prints)
                try:
                    with open(prints) as f:
                        img_print = Image(prints, 8.25*inch, 6.25*inch)
                        self.story.append(img_print)
                        f.close()
                except IOError:
                    print "No Print for {0}".format(unicode(prints))
            self.story.append(FrameBreak())
            self.story.append(FrameBreak())

            #Bottom barcode
            self.story.append(code)
            self.story.append(text_code)
            try:
                hot = row_data[q+1].value(8).toString()
            except:
                hot = "0"
            if hot == "0":
                self.story.append(NextPageTemplate("main"))
            else:
                self.story.append(NextPageTemplate("hot"))
            self.story.append(flowables.PageBreak())

    def build(self):
        self.doc.build(self.story)
