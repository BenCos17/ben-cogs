"""
Export utilities for SkySearch cog
"""

import os
import csv
import tempfile
import datetime
import discord
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle


class ExportManager:
    """Manages export functionality for SkySearch."""
    
    def __init__(self, cog):
        self.cog = cog
    
    async def export_aircraft_data(self, all_aircraft, search_type, search_value, file_format, ctx):
        """Export aircraft data to various formats."""
        if not all_aircraft:
            embed = discord.Embed(title="Error", description="No aircraft data found.", color=0xfa4545)
            await ctx.send(embed=embed)
            return None, None

        aircraft_count = len(all_aircraft)
        file_name = f"{search_type}_{search_value.replace(' ', '_')}_{aircraft_count}_aircraft.{file_format.lower()}"
        file_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            if file_format.lower() == "csv":
                await self._export_csv(all_aircraft, file_path)
            elif file_format.lower() == "pdf":
                await self._export_pdf(all_aircraft, file_path, search_type, search_value, aircraft_count)
            elif file_format.lower() in ["txt"]:
                await self._export_txt(all_aircraft, file_path)
            elif file_format.lower() == "html":
                await self._export_html(all_aircraft, file_path)
            else:
                embed = discord.Embed(title="Error", description="Invalid file format specified. Use one of: csv, pdf, txt, or html.", color=0xfa4545)
                await ctx.send(embed=embed)
                return None, None

        except PermissionError as e:
            embed = discord.Embed(title="Error", description="I do not have permission to write to the file system.", color=0xff4545)
            await ctx.send(embed=embed)
            if os.path.exists(file_path):
                os.remove(file_path)
            return None, None

        return file_path, aircraft_count

    async def _export_csv(self, all_aircraft, file_path):
        """Export aircraft data to CSV format."""
        with open(file_path, "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            aircraft_keys = list(all_aircraft[0].keys())
            writer.writerow([key.upper() for key in aircraft_keys])
            for aircraft in all_aircraft:
                aircraft_values = list(map(str, aircraft.values()))
                writer.writerow(aircraft_values)

    async def _export_pdf(self, all_aircraft, file_path, search_type, search_value, aircraft_count):
        """Export aircraft data to PDF format."""
        doc = SimpleDocTemplate(file_path, pagesize=landscape(A4)) 
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Normal-Bold', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=1)) 
        styles.add(ParagraphStyle(name='Normal-Small', fontName='Helvetica', fontSize=6, leading=8, alignment=1))
        flowables = []

        # Add title and summary
        flowables.append(Paragraph(f"<u>Aircraft Export Report</u>", styles['Normal-Bold'])) 
        flowables.append(Spacer(1, 12))
        flowables.append(Paragraph(f"Search Type: {search_type.capitalize()}", styles['Normal-Small']))
        flowables.append(Paragraph(f"Search Value: {search_value}", styles['Normal-Small']))
        flowables.append(Paragraph(f"Total Aircraft: {aircraft_count}", styles['Normal-Small']))
        flowables.append(Paragraph(f"Export Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal-Small']))
        flowables.append(Spacer(1, 24)) 

        # Always use a limited set of essential columns for PDF to avoid layout issues
        essential_keys = ['hex', 'flight', 'reg', 't', 'alt_baro', 'lat', 'lon']
        
        # Check which essential keys are actually available in the data
        available_keys = []
        for key in essential_keys:
            if key in all_aircraft[0].keys():
                available_keys.append(key)
        
        # If no essential keys are available, use the first few keys from the data
        if not available_keys:
            all_keys = list(all_aircraft[0].keys())
            available_keys = all_keys[:7]  # Limit to first 7 columns
        
        # Create table with selected aircraft data
        table_data = [[Paragraph(f"<b>{key.upper()}</b>", styles['Normal-Bold']) for key in available_keys]]
        
        for aircraft in all_aircraft:
            aircraft_values = []
            for key in available_keys:
                value = str(aircraft.get(key, 'N/A'))
                # Truncate long values to prevent layout issues
                if len(value) > 15:
                    value = value[:12] + "..."
                aircraft_values.append(Paragraph(value, styles['Normal-Small']))
            table_data.append(aircraft_values)

        # Create table with smaller font and tighter spacing
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        flowables.append(table)
        
        # Add note about limited columns
        flowables.append(Spacer(1, 12))
        flowables.append(Paragraph(f"Note: Only essential columns shown. Full data available in CSV format.", styles['Normal-Small']))
        
        doc.build(flowables)

    async def _export_txt(self, all_aircraft, file_path):
        """Export aircraft data to TXT format."""
        with open(file_path, "w", newline='', encoding='utf-8') as file:
            aircraft_keys = list(all_aircraft[0].keys())
            file.write(' '.join([key.upper() for key in aircraft_keys]) + '\n')
            for aircraft in all_aircraft:
                aircraft_values = list(map(str, aircraft.values()))
                file.write(' '.join(aircraft_values) + '\n')

    async def _export_html(self, all_aircraft, file_path):
        """Export aircraft data to HTML format."""
        with open(file_path, "w", newline='', encoding='utf-8') as file:
            aircraft_keys = list(all_aircraft[0].keys())
            file.write('<table>\n')
            file.write('<tr>\n')
            for key in aircraft_keys:
                file.write(f'<th>{key.upper()}</th>\n')
            file.write('</tr>\n')
            for aircraft in all_aircraft:
                aircraft_values = list(map(str, aircraft.values()))
                file.write('<tr>\n')
                for value in aircraft_values:
                    file.write(f'<td>{value}</td>\n')
                file.write('</tr>\n')
            file.write('</table>\n') 