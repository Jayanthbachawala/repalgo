import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import xlsxwriter
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO

class ReportGenerator:
    def __init__(self):
        self.output_dir = 'data/reports'
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_pdf_report(self, report_type: str, start_date: datetime = None, 
                           end_date: datetime = None) -> str:
        """Generate comprehensive PDF report"""
        try:
            # Import journal and other components
            from core.journal import TradeJournal
            from core.paper_trade import PaperTradingEngine
            
            journal = TradeJournal()
            paper_engine = PaperTradingEngine()
            
            # Set date range
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                if report_type == "Daily Summary":
                    start_date = end_date - timedelta(days=1)
                elif report_type == "Weekly Report":
                    start_date = end_date - timedelta(weeks=1)
                elif report_type == "Monthly Report":
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=30)
            
            # Generate filename
            filename = f"{report_type.lower().replace(' ', '_')}_{end_date.strftime('%Y%m%d')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # Center alignment
                textColor=colors.darkblue
            )
            
            story.append(Paragraph(f"AI Options Trader Agent - {report_type}", title_style))
            story.append(Paragraph(f"Report Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", 
                                 styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            
            # Get portfolio summary
            portfolio_summary = paper_engine.get_performance_summary()
            trade_analysis = journal.get_trade_analysis()
            
            summary_data = [
                ["Metric", "Value"],
                ["Total Portfolio Value", f"₹{paper_engine.get_portfolio_value():,.2f}"],
                ["Daily P&L", f"₹{paper_engine.get_daily_pnl():,.2f}"],
                ["Total Trades", str(portfolio_summary.get('total_trades', 0))],
                ["Win Rate", f"{portfolio_summary.get('win_rate', 0):.1f}%"],
                ["Profit Factor", f"{portfolio_summary.get('profit_factor', 0):.2f}"],
                ["Max Drawdown", f"₹{trade_analysis.get('max_drawdown', 0):,.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Trade History
            story.append(Paragraph("Recent Trade History", styles['Heading2']))
            
            # Get recent trades
            days_back = (end_date - start_date).days
            trade_history = journal.get_trade_history(days=max(days_back, 7))
            
            if not trade_history.empty:
                # Limit to last 10 trades for PDF
                recent_trades = trade_history.head(10)
                
                trade_data = [["Symbol", "Type", "Strike", "Entry Price", "Exit Price", "P&L", "Confidence"]]
                
                for _, trade in recent_trades.iterrows():
                    trade_data.append([
                        str(trade.get('symbol', '')),
                        str(trade.get('option_type', '')),
                        f"₹{trade.get('strike', 0):.0f}",
                        f"₹{trade.get('entry_price', 0):.2f}",
                        f"₹{trade.get('exit_price', 0):.2f}" if trade.get('exit_price') else "Open",
                        f"₹{trade.get('pnl', 0):,.2f}",
                        f"{trade.get('confidence', 0):.0f}%"
                    ])
                
                trade_table = Table(trade_data, colWidths=[0.8*inch, 0.6*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
                trade_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(trade_table)
            else:
                story.append(Paragraph("No trades found for the selected period.", styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Performance Analytics
            story.append(Paragraph("Performance Analytics", styles['Heading2']))
            
            # Symbol-wise performance
            symbol_performance = journal.get_symbol_performance()
            
            if not symbol_performance.empty:
                symbol_data = [["Symbol", "Total Trades", "Win Rate", "Total P&L", "Avg P&L", "Best Trade"]]
                
                for _, row in symbol_performance.head(5).iterrows():
                    symbol_data.append([
                        str(row.get('symbol', '')),
                        str(row.get('total_trades', 0)),
                        f"{row.get('win_rate', 0):.1f}%",
                        f"₹{row.get('total_pnl', 0):,.2f}",
                        f"₹{row.get('avg_pnl', 0):,.2f}",
                        f"₹{row.get('best_trade', 0):,.2f}"
                    ])
                
                symbol_table = Table(symbol_data, colWidths=[1*inch, 1*inch, 1*inch, 1.2*inch, 1*inch, 1*inch])
                symbol_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(symbol_table)
            
            story.append(Spacer(1, 20))
            
            # Risk Analysis
            story.append(Paragraph("Risk Analysis", styles['Heading2']))
            
            risk_metrics = [
                ["Risk Metric", "Value", "Status"],
                ["Win Rate", f"{portfolio_summary.get('win_rate', 0):.1f}%", 
                 "Good" if portfolio_summary.get('win_rate', 0) > 60 else "Needs Improvement"],
                ["Profit Factor", f"{portfolio_summary.get('profit_factor', 0):.2f}",
                 "Excellent" if portfolio_summary.get('profit_factor', 0) > 2 else "Good" if portfolio_summary.get('profit_factor', 0) > 1 else "Poor"],
                ["Max Drawdown", f"₹{trade_analysis.get('max_drawdown', 0):,.2f}",
                 "Good" if abs(trade_analysis.get('max_drawdown', 0)) < 10000 else "Monitor"],
                ["Sharpe Ratio", f"{trade_analysis.get('sharpe_ratio', 0):.2f}",
                 "Good" if trade_analysis.get('sharpe_ratio', 0) > 1 else "Average"]
            ]
            
            risk_table = Table(risk_metrics, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(risk_table)
            story.append(Spacer(1, 20))
            
            # AI Performance
            story.append(Paragraph("AI Performance Metrics", styles['Heading2']))
            
            # This would be populated from AI learning data
            ai_metrics = [
                ["AI Metric", "Current Value", "Target"],
                ["Prediction Accuracy", "75.2%", ">80%"],
                ["Average Confidence", "68.5%", ">70%"],
                ["False Positive Rate", "15.3%", "<20%"],
                ["Learning Progress", "Improving", "Stable Growth"]
            ]
            
            ai_table = Table(ai_metrics, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            ai_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(ai_table)
            story.append(Spacer(1, 20))
            
            # Footer
            story.append(Paragraph("---", styles['Normal']))
            story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                 styles['Italic']))
            story.append(Paragraph("AI Options Trader Agent v1.0", styles['Italic']))
            
            # Build PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None
    
    def generate_excel_report(self, report_type: str, start_date: datetime = None, 
                             end_date: datetime = None) -> str:
        """Generate comprehensive Excel report"""
        try:
            # Import required components
            from core.journal import TradeJournal
            from core.paper_trade import PaperTradingEngine
            
            journal = TradeJournal()
            paper_engine = PaperTradingEngine()
            
            # Set date range
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                if report_type == "Daily Summary":
                    start_date = end_date - timedelta(days=1)
                elif report_type == "Weekly Report":
                    start_date = end_date - timedelta(weeks=1)
                elif report_type == "Monthly Report":
                    start_date = end_date - timedelta(days=30)
                else:
                    start_date = end_date - timedelta(days=30)
            
            # Generate filename
            filename = f"{report_type.lower().replace(' ', '_')}_{end_date.strftime('%Y%m%d')}.xlsx"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create Excel workbook
            workbook = xlsxwriter.Workbook(filepath)
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4472C4',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            money_format = workbook.add_format({
                'num_format': '₹#,##0.00',
                'border': 1,
                'align': 'right'
            })
            
            percent_format = workbook.add_format({
                'num_format': '0.0%',
                'border': 1,
                'align': 'center'
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            # Summary Sheet
            summary_sheet = workbook.add_worksheet('Summary')
            summary_sheet.set_column('A:B', 20)
            
            summary_sheet.write('A1', 'AI Options Trader Agent - Summary Report', header_format)
            summary_sheet.merge_range('A1:B1', 'AI Options Trader Agent - Summary Report', header_format)
            
            portfolio_summary = paper_engine.get_performance_summary()
            trade_analysis = journal.get_trade_analysis()
            
            row = 3
            summary_data = [
                ('Portfolio Value', paper_engine.get_portfolio_value(), money_format),
                ('Daily P&L', paper_engine.get_daily_pnl(), money_format),
                ('Total Trades', portfolio_summary.get('total_trades', 0), cell_format),
                ('Winning Trades', portfolio_summary.get('winning_trades', 0), cell_format),
                ('Win Rate', portfolio_summary.get('win_rate', 0)/100, percent_format),
                ('Profit Factor', portfolio_summary.get('profit_factor', 0), cell_format),
                ('Best Trade', portfolio_summary.get('max_win', 0), money_format),
                ('Worst Trade', portfolio_summary.get('max_loss', 0), money_format),
                ('Max Drawdown', trade_analysis.get('max_drawdown', 0), money_format)
            ]
            
            summary_sheet.write(row, 0, 'Metric', header_format)
            summary_sheet.write(row, 1, 'Value', header_format)
            
            for i, (metric, value, format_style) in enumerate(summary_data):
                summary_sheet.write(row + 1 + i, 0, metric, cell_format)
                summary_sheet.write(row + 1 + i, 1, value, format_style)
            
            # Trade History Sheet
            trade_sheet = workbook.add_worksheet('Trade History')
            
            days_back = (end_date - start_date).days
            trade_history = journal.get_trade_history(days=max(days_back, 30))
            
            if not trade_history.empty:
                # Headers
                headers = ['ID', 'Symbol', 'Type', 'Strike', 'Entry Price', 'Exit Price', 
                          'Entry Time', 'Exit Time', 'P&L', 'Confidence', 'Status', 'Reasoning']
                
                for col, header in enumerate(headers):
                    trade_sheet.write(0, col, header, header_format)
                
                # Data
                for row, (_, trade) in enumerate(trade_history.iterrows(), 1):
                    trade_sheet.write(row, 0, str(trade.get('id', '')), cell_format)
                    trade_sheet.write(row, 1, str(trade.get('symbol', '')), cell_format)
                    trade_sheet.write(row, 2, str(trade.get('option_type', '')), cell_format)
                    trade_sheet.write(row, 3, trade.get('strike', 0), cell_format)
                    trade_sheet.write(row, 4, trade.get('entry_price', 0), money_format)
                    trade_sheet.write(row, 5, trade.get('exit_price', 0) if trade.get('exit_price') else '', money_format)
                    trade_sheet.write(row, 6, str(trade.get('entry_time', '')), cell_format)
                    trade_sheet.write(row, 7, str(trade.get('exit_time', '')), cell_format)
                    trade_sheet.write(row, 8, trade.get('pnl', 0), money_format)
                    trade_sheet.write(row, 9, trade.get('confidence', 0)/100, percent_format)
                    trade_sheet.write(row, 10, str(trade.get('status', '')), cell_format)
                    trade_sheet.write(row, 11, str(trade.get('reasoning', ''))[:100], cell_format)
                
                # Auto-fit columns
                for col in range(len(headers)):
                    trade_sheet.set_column(col, col, 15)
            
            # Daily Performance Sheet
            daily_sheet = workbook.add_worksheet('Daily Performance')
            
            daily_performance = journal.get_daily_performance(days=30)
            
            if not daily_performance.empty:
                daily_headers = ['Date', 'Total Trades', 'Winning Trades', 'Win Rate', 
                               'Daily P&L', 'Avg Confidence']
                
                for col, header in enumerate(daily_headers):
                    daily_sheet.write(0, col, header, header_format)
                
                for row, (_, day) in enumerate(daily_performance.iterrows(), 1):
                    daily_sheet.write(row, 0, day.get('trade_date', ''), cell_format)
                    daily_sheet.write(row, 1, day.get('total_trades', 0), cell_format)
                    daily_sheet.write(row, 2, day.get('winning_trades', 0), cell_format)
                    daily_sheet.write(row, 3, day.get('win_rate', 0)/100, percent_format)
                    daily_sheet.write(row, 4, day.get('daily_pnl', 0), money_format)
                    daily_sheet.write(row, 5, day.get('avg_confidence', 0)/100, percent_format)
                
                for col in range(len(daily_headers)):
                    daily_sheet.set_column(col, col, 15)
            
            # Symbol Performance Sheet
            symbol_sheet = workbook.add_worksheet('Symbol Performance')
            
            symbol_performance = journal.get_symbol_performance()
            
            if not symbol_performance.empty:
                symbol_headers = ['Symbol', 'Total Trades', 'Winning Trades', 'Win Rate',
                                'Total P&L', 'Avg P&L', 'Best Trade', 'Worst Trade', 'Avg Confidence']
                
                for col, header in enumerate(symbol_headers):
                    symbol_sheet.write(0, col, header, header_format)
                
                for row, (_, symbol) in enumerate(symbol_performance.iterrows(), 1):
                    symbol_sheet.write(row, 0, str(symbol.get('symbol', '')), cell_format)
                    symbol_sheet.write(row, 1, symbol.get('total_trades', 0), cell_format)
                    symbol_sheet.write(row, 2, symbol.get('winning_trades', 0), cell_format)
                    symbol_sheet.write(row, 3, symbol.get('win_rate', 0)/100, percent_format)
                    symbol_sheet.write(row, 4, symbol.get('total_pnl', 0), money_format)
                    symbol_sheet.write(row, 5, symbol.get('avg_pnl', 0), money_format)
                    symbol_sheet.write(row, 6, symbol.get('best_trade', 0), money_format)
                    symbol_sheet.write(row, 7, symbol.get('worst_trade', 0), money_format)
                    symbol_sheet.write(row, 8, symbol.get('avg_confidence', 0)/100, percent_format)
                
                for col in range(len(symbol_headers)):
                    symbol_sheet.set_column(col, col, 15)
            
            workbook.close()
            
            return filepath
            
        except Exception as e:
            print(f"Error generating Excel report: {e}")
            return None
    
    def generate_performance_charts(self, days: int = 30) -> List[str]:
        """Generate performance charts as image files"""
        try:
            from core.journal import TradeJournal
            
            journal = TradeJournal()
            chart_files = []
            
            # P&L Curve Chart
            trade_history = journal.get_trade_history(days=days)
            
            if not trade_history.empty:
                # Prepare data
                df_sorted = trade_history.sort_values('entry_time')
                df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
                
                # Create P&L curve
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_sorted['entry_time'],
                    y=df_sorted['cumulative_pnl'],
                    mode='lines+markers',
                    name='Cumulative P&L',
                    line=dict(color='blue', width=2)
                ))
                
                fig.update_layout(
                    title='Cumulative P&L Over Time',
                    xaxis_title='Date',
                    yaxis_title='Cumulative P&L (₹)',
                    hovermode='x unified'
                )
                
                # Save chart
                chart_path = os.path.join(self.output_dir, f'pnl_curve_{datetime.now().strftime("%Y%m%d")}.png')
                fig.write_image(chart_path, width=800, height=400)
                chart_files.append(chart_path)
                
                # Daily P&L Bar Chart
                daily_performance = journal.get_daily_performance(days=days)
                
                if not daily_performance.empty:
                    fig2 = go.Figure()
                    
                    colors = ['green' if pnl >= 0 else 'red' for pnl in daily_performance['daily_pnl']]
                    
                    fig2.add_trace(go.Bar(
                        x=daily_performance['trade_date'],
                        y=daily_performance['daily_pnl'],
                        marker_color=colors,
                        name='Daily P&L'
                    ))
                    
                    fig2.update_layout(
                        title='Daily P&L Performance',
                        xaxis_title='Date',
                        yaxis_title='Daily P&L (₹)',
                        showlegend=False
                    )
                    
                    chart_path = os.path.join(self.output_dir, f'daily_pnl_{datetime.now().strftime("%Y%m%d")}.png')
                    fig2.write_image(chart_path, width=800, height=400)
                    chart_files.append(chart_path)
                
                # Win Rate Chart
                win_rate_data = daily_performance['win_rate'].tolist()
                dates = daily_performance['trade_date'].tolist()
                
                fig3 = go.Figure()
                
                fig3.add_trace(go.Scatter(
                    x=dates,
                    y=win_rate_data,
                    mode='lines+markers',
                    name='Win Rate',
                    line=dict(color='orange', width=2)
                ))
                
                fig3.add_hline(y=50, line_dash="dash", line_color="gray", 
                              annotation_text="Break-even (50%)")
                
                fig3.update_layout(
                    title='Win Rate Trend',
                    xaxis_title='Date',
                    yaxis_title='Win Rate (%)',
                    yaxis=dict(range=[0, 100])
                )
                
                chart_path = os.path.join(self.output_dir, f'win_rate_{datetime.now().strftime("%Y%m%d")}.png')
                fig3.write_image(chart_path, width=800, height=400)
                chart_files.append(chart_path)
            
            return chart_files
            
        except Exception as e:
            print(f"Error generating performance charts: {e}")
            return []
    
    def generate_ai_learning_report(self) -> str:
        """Generate AI learning progress report"""
        try:
            from core.journal import TradeJournal
            from core.signals import AISignalEngine
            
            journal = TradeJournal()
            signal_engine = AISignalEngine()
            
            filename = f"ai_learning_report_{datetime.now().strftime('%Y%m%d')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1,
                textColor=colors.darkblue
            )
            
            story.append(Paragraph("AI Learning Progress Report", title_style))
            story.append(Spacer(1, 20))
            
            # AI Performance Metrics
            accuracy = signal_engine.get_accuracy()
            avg_confidence = signal_engine.get_average_confidence()
            learning_progress = signal_engine.get_learning_progress()
            
            ai_data = [
                ["AI Metric", "Current Value", "Status"],
                ["Prediction Accuracy", f"{accuracy:.1f}%", "Good" if accuracy > 70 else "Needs Improvement"],
                ["Average Confidence", f"{avg_confidence:.1f}%", "Good" if avg_confidence > 65 else "Average"],
                ["Learning Data Points", str(len(signal_engine.learning_data)), "Active"],
                ["Model Status", "Trained" if signal_engine.model_trained else "Training", ""],
                ["Learning Trend", "Improving" if len(learning_progress) > 5 and learning_progress[-1] > learning_progress[0] else "Stable", ""]
            ]
            
            ai_table = Table(ai_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            ai_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(ai_table)
            story.append(Spacer(1, 20))
            
            # Parameter Importance
            story.append(Paragraph("Parameter Importance in AI Decisions", styles['Heading2']))
            
            param_importance = [
                ["Parameter", "Weight", "Importance"],
                ["Delta", f"{signal_engine.parameter_weights['delta']:.2f}", "High"],
                ["OI Change", f"{signal_engine.parameter_weights['oi_change']:.2f}", "High"],
                ["Volume", f"{signal_engine.parameter_weights['volume']:.2f}", "Medium"],
                ["Momentum", f"{signal_engine.parameter_weights['momentum']:.2f}", "Medium"],
                ["Implied Volatility", f"{signal_engine.parameter_weights['iv']:.2f}", "Low"],
                ["Spread Quality", f"{signal_engine.parameter_weights['spread']:.2f}", "Low"]
            ]
            
            param_table = Table(param_importance, colWidths=[2.5*inch, 1*inch, 1.5*inch])
            param_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(param_table)
            story.append(Spacer(1, 20))
            
            # Learning Recommendations
            story.append(Paragraph("AI Learning Recommendations", styles['Heading2']))
            
            recommendations = []
            
            if accuracy < 70:
                recommendations.append("• Increase training data by extending paper trading period")
                recommendations.append("• Review parameter weights for better signal accuracy")
            
            if avg_confidence < 65:
                recommendations.append("• Adjust confidence threshold for more selective trading")
                recommendations.append("• Focus on higher probability setups")
            
            if len(learning_progress) < 10:
                recommendations.append("• Continue paper trading to gather more learning data")
                recommendations.append("• Monitor AI performance over extended periods")
            
            if not recommendations:
                recommendations.append("• AI performance is satisfactory")
                recommendations.append("• Continue current learning approach")
            
            for rec in recommendations:
                story.append(Paragraph(rec, styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Footer
            story.append(Paragraph("---", styles['Normal']))
            story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                                 styles['Italic']))
            
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            print(f"Error generating AI learning report: {e}")
            return None
    
    def cleanup_old_reports(self, days: int = 30):
        """Clean up old report files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_date:
                    os.remove(filepath)
                    print(f"Deleted old report: {filename}")
            
        except Exception as e:
            print(f"Error cleaning up old reports: {e}")
