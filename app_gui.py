import sys
import requests
from datetime import date
from typing import Any, Dict, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class EPSSViewer(QMainWindow):
    API_URL = "https://api.first.org/data/v1/epss"
    BACKGROUND_COLOR = "#2e2e2e"
    INPUT_COLOR = "#3e3e3e"
    BUTTON_COLOR = "#007acc"
    TEXT_COLOR = "#ffffff"

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("EPSS Viewer")
        self.setGeometry(200, 200, 600, 500)
        self.setStyleSheet(f"background-color: {self.BACKGROUND_COLOR}; color: {self.TEXT_COLOR};")

        # Main container and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Panels layout
        panels_layout = QHBoxLayout()
        self.init_left_panel(panels_layout)
        self.init_right_panel(panels_layout)

        main_layout.addLayout(panels_layout)

    def init_left_panel(self, layout: QHBoxLayout):
        """Initialize the left panel with input fields and buttons."""
        self.left_panel = QVBoxLayout()

        self.cve_input = QLineEdit()
        self.cve_input.setPlaceholderText("Enter CVE (e.g., CVE-2023-1234)")
        self.cve_input.setStyleSheet(f"background-color: {self.INPUT_COLOR}; color: {self.TEXT_COLOR}; padding: 5px; border-radius: 5px;")

        self.add_button = QPushButton("Add CVE")
        self.add_button.setStyleSheet(f"background-color: {self.BUTTON_COLOR}; color: {self.TEXT_COLOR}; padding: 5px; border-radius: 5px;")
        self.add_button.clicked.connect(self.add_cve)

        self.cve_list = QListWidget()
        self.cve_list.setStyleSheet(f"background-color: {self.INPUT_COLOR}; color: {self.TEXT_COLOR}; border-radius: 5px;")

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.setStyleSheet(f"background-color: {self.BUTTON_COLOR}; color: {self.TEXT_COLOR}; padding: 5px; border-radius: 5px;")
        self.calculate_button.clicked.connect(self.calculate_epss)

        self.left_panel.addWidget(self.cve_input)
        self.left_panel.addWidget(self.add_button)
        self.left_panel.addWidget(self.cve_list)
        self.left_panel.addStretch()
        self.left_panel.addWidget(self.calculate_button)

        layout.addLayout(self.left_panel, 1)

    def init_right_panel(self, layout: QHBoxLayout):
        """Initialize the right panel with a graph and output label."""
        self.right_panel = QVBoxLayout()

        # Bell curve visualization
        self.bell_curve_widget = FigureCanvas(Figure(figsize=(6, 4)))
        self.ax = self.bell_curve_widget.figure.add_subplot(111)
        self.right_panel.addWidget(self.bell_curve_widget)

        # EPSS score display
        self.epss_score_label = QLabel("EPSS Score: X    Percentile: XX")
        self.epss_score_label.setAlignment(Qt.AlignCenter)
        self.epss_score_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        self.right_panel.addWidget(self.epss_score_label)

        layout.addLayout(self.right_panel, 3)

    def add_cve(self):
        """Add a valid CVE to the list."""
        cve_text = self.cve_input.text().strip()
        if self.is_valid_cve(cve_text):
            self.cve_list.addItem(cve_text)
            self.cve_input.clear()
        else:
            self.epss_score_label.setText("Invalid CVE format. Please try again.")

    @staticmethod
    def is_valid_cve(cve: str) -> bool:
        """Validate the format of a CVE ID."""
        return bool(cve.startswith("CVE-") and len(cve.split("-")) == 3 and cve.split("-")[1].isdigit() and cve.split("-")[2].isdigit())

    @staticmethod
    def get_current_date() -> str:
        """Return the current date in YYYY-MM-DD format."""
        return date.today().strftime("%Y-%m-%d")

    def fetch_epss_data(self, cve: str, query_date: str) -> Optional[Dict[str, Any]]:
        """Fetch EPSS data for a given CVE and date."""
        params = {"cve": cve, "date": query_date, "envelope": "true", "pretty": "true"}
        try:
            response = requests.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.epss_score_label.setText(f"Error fetching data: {str(e)}")
            return None

    def calculate_epss(self):
        """Calculate and display EPSS data for the selected CVE."""
        selected_items = self.cve_list.selectedItems()
        if not selected_items:
            self.epss_score_label.setText("Please select a CVE from the list.")
            return

        cve_id = selected_items[0].text()
        query_date = self.get_current_date()
        result = self.fetch_epss_data(cve_id, query_date)

        if not result or "data" not in result or not result["data"]:
            self.epss_score_label.setText("No data available or invalid API response.")
            return

        try:
            epss_score = float(result["data"][0]["epss"])
            percentile = float(result["data"][0]["percentile"]) * 100
            self.epss_score_label.setText(f"EPSS Score: {epss_score:.4f}    Percentile: {percentile:.2f}")
            self.plot_bell_curve(epss_score)
        except (KeyError, ValueError, IndexError):
            self.epss_score_label.setText("Error processing API response.")

    def plot_bell_curve(self, epss_score: float):
        """Render a bell curve with the EPSS score."""
        x = np.linspace(0, 1, 500)
        y = np.exp(-((x - 0.5) ** 2) / (2 * 0.1 ** 2))
        self.ax.clear()
        self.ax.plot(x, y, label="Bell Curve")
        self.ax.axvline(epss_score, color="r", linestyle="--", label=f"EPSS Score: {epss_score:.4f}")
        self.ax.set_title("EPSS Score Distribution")     
        self.ax.set_xlabel("Score")
        self.ax.set_ylabel("Density")
        self.bell_curve_widget.draw()


def run_gui():
    app = QApplication(sys.argv)
    window = EPSSViewer()
    window.show()
    sys.exit(app.exec())
