import sys
import os
import json
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QListWidget, QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QFont


class CourseScheduler(QMainWindow):
    """Main window for visualizing ITU course schedules."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ITU Course Scheduler")
        self.setGeometry(200, 200, 842, 450)

        self.json_data = {}  # Will hold the loaded JSON data
        self.selected_crns = []  # List of selected CRNs to visualize
        self.color_map = {}  # Maps CRNs to QColor for consistent block coloring
        self.pastel_colors = self.get_pastel_colors()  # Predefined pastel colors

        self.init_ui()
        self.load_state()

    def init_ui(self):
        self.set_dark_theme()

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        # ------- LEFT PANEL -------
        left_panel = QVBoxLayout()

        # Department selection
        left_panel.addWidget(QLabel("Select Department:"))
        self.department_selector = QComboBox()
        self.load_departments()
        self.department_selector.currentIndexChanged.connect(self.load_schedule_data)
        left_panel.addWidget(self.department_selector)

        # CRN input
        self.crn_input = QLineEdit()
        self.crn_input.setPlaceholderText("Enter CRN (e.g. 20540)")
        add_crn_button = QPushButton("Add CRN")
        add_crn_button.clicked.connect(self.add_crn)

        crn_input_layout = QHBoxLayout()
        crn_input_layout.addWidget(self.crn_input)
        crn_input_layout.addWidget(add_crn_button)

        left_panel.addWidget(QLabel("CRN Input:"))
        left_panel.addLayout(crn_input_layout)

        # Selected CRNs list with remove functionality
        left_panel.addWidget(QLabel("Selected CRNs:"))
        self.crn_list = QListWidget()
        left_panel.addWidget(self.crn_list)

        remove_crn_button = QPushButton("Remove Selected CRN")
        remove_crn_button.clicked.connect(self.remove_crn)
        left_panel.addWidget(remove_crn_button)

        # Save chart button
        save_button = QPushButton("Save Chart")
        save_button.clicked.connect(self.save_chart)
        left_panel.addWidget(save_button)

        # Course details label
        self.course_details_label = QLabel("Course Details:")
        self.course_details_label.setWordWrap(True)
        self.course_details_label.setMinimumHeight(100)
        left_panel.addWidget(self.course_details_label)

        main_layout.addLayout(left_panel, 2)

        # ------- SCHEDULE TABLE -------
        self.schedule_table = QTableWidget(10, 5)  # 10 time slots, 5 weekdays
        self.schedule_table.setHorizontalHeaderLabels(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
        time_labels = []
        start_hour = 8
        for i in range(10):
            hour_label = f"{start_hour + i}:30 - {start_hour + i + 1}:30"
            time_labels.append(hour_label)
        self.schedule_table.setVerticalHeaderLabels(time_labels)
        self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Connect cell click to show course details
        self.schedule_table.cellClicked.connect(self.on_cell_clicked)

        main_layout.addWidget(self.schedule_table, 5)

        self.setCentralWidget(main_widget)

    def set_dark_theme(self):
        """Applies a dark theme to the entire application."""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        QApplication.instance().setPalette(dark_palette)

    def load_departments(self):
        """Populate the department selector with the .json files in the 'data' directory."""
        self.department_selector.addItem("Select Department")
        for file in os.listdir("data"):
            if file.endswith(".json"):
                department_name = file.replace(".json", "")
                self.department_selector.addItem(department_name)

    def load_schedule_data(self):
        """Load the schedule data from the selected department's JSON file."""
        selected_dept = self.department_selector.currentText()
        if selected_dept == "Select Department":
            return

        file_path = os.path.join("data", selected_dept + ".json")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.json_data = {}

        self.update_schedule()

    def add_crn(self):
        """Add a CRN to the selected list and refresh the schedule."""
        crn = self.crn_input.text().strip()
        if crn.isdigit():
            if crn not in self.selected_crns:
                self.selected_crns.append(crn)
                course_code = self.get_course_code(crn)
                self.crn_list.addItem(f"{crn} - {course_code}")
            self.crn_input.clear()
            self.update_schedule()
        else:
            QMessageBox.warning(self, "Invalid Input", "CRN must be numeric.")

    def remove_crn(self):
        """Remove the selected CRN from the list and update the schedule."""
        selected_item = self.crn_list.currentItem()
        if selected_item:
            crn_text = selected_item.text()
            crn = crn_text.split(" - ")[0]
            self.selected_crns.remove(crn)
            self.crn_list.takeItem(self.crn_list.row(selected_item))
            self.update_schedule()

    def update_schedule(self):
        """Clear and reconstruct the schedule table based on selected CRNs."""
        self.schedule_table.clearContents()
        for row in range(self.schedule_table.rowCount()):
            for col in range(self.schedule_table.columnCount()):
                self.schedule_table.setSpan(row, col, 1, 1)

        for course in self.json_data.get("dersProgramList", []):
            if course["crn"] in self.selected_crns:
                self.add_course_blocks(course)

    def add_course_blocks(self, course):
        """Create table blocks for the given course (which may span multiple days/times)."""
        days = course["gunAdiEN"].split()
        times = course["baslangicSaati"].split()

        crn = course["crn"]
        if crn not in self.color_map:
            self.color_map[crn] = self.pastel_colors.pop()

        for day, time_range in zip(days, times):
            start_str, end_str = time_range.split("/")
            start_row = self.time_to_row_index(start_str)
            end_row = self.time_to_row_index(end_str)
            col = self.get_day_index(day)
            if start_row is None or end_row is None or col is None:
                continue

            row_span = end_row - start_row + 1
            if self.schedule_table.item(start_row, col):
                existing_item = self.schedule_table.item(start_row, col)
                existing_item.setBackground(QColor("red"))
                existing_item.setToolTip("Overlapping Courses!")
                existing_item.setFont(QFont("Arial", weight=QFont.Weight.Bold))
                return

            self.schedule_table.setSpan(start_row, col, row_span, 1)
            item = QTableWidgetItem(course["dersKodu"])
            item.setForeground(QColor("black"))  # Change text color to black
            item.setBackground(self.color_map[crn])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, course)
            self.schedule_table.setItem(start_row, col, item)

    def time_to_row_index(self, time_str):
        """Convert a time string like '08:30' into a row index."""
        try:
            hour, minute = map(int, time_str.split(":"))
        except ValueError:
            return None
        total_minutes = (hour * 60) + minute
        start_minutes = (8 * 60) + 30
        diff = total_minutes - start_minutes
        row = diff // 60
        return row if 0 <= row < 10 else None

    def get_day_index(self, day):
        """Return the column index for a given weekday."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        return days.index(day) if day in days else None

    def get_course_code(self, crn):
        """Get course code for a given CRN."""
        for course in self.json_data.get("dersProgramList", []):
            if course["crn"] == crn:
                return course["dersKodu"]
        return "Unknown"

    def get_pastel_colors(self):
        """Generate 15 predefined pastel colors."""
        colors = [
            QColor(255, 179, 186), QColor(255, 223, 186), QColor(255, 255, 186),
            QColor(186, 255, 201), QColor(186, 225, 255), QColor(255, 186, 255),
            QColor(179, 186, 255), QColor(255, 200, 200), QColor(200, 255, 200),
            QColor(200, 200, 255), QColor(255, 255, 200), QColor(200, 255, 255),
            QColor(255, 200, 255), QColor(230, 230, 250), QColor(250, 235, 215)
        ]
        random.shuffle(colors)
        return colors

    def on_cell_clicked(self, row, column):
        """Show course details when a table cell is clicked."""
        item = self.schedule_table.item(row, column)
        if item:
            course = item.data(Qt.ItemDataRole.UserRole)
            self.course_details_label.setText(self.format_course_details(course))

    def format_course_details(self, course):
        """Return a formatted string for course details."""
        return (
            f"Course Code: {course['dersKodu']}\n"
            f"Course Name: {course['dersAdi']}\n"
            f"Instructor: {course['adSoyad']}\n"
            f"Location: {course['mekanAdi']}\n"
            f"Days: {course['gunAdiEN']}\n"
            f"Time: {course['baslangicSaati']}"
        )

    def save_chart(self):
        """Save the chart as an image."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Schedule Chart", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            pixmap = self.grab()
            pixmap.save(file_path)

    def save_state(self):
        """Save selected CRNs to a JSON file."""
        with open("state.json", "w") as f:
            json.dump({"selected_crns": self.selected_crns}, f)

    def load_state(self):
        """Load selected CRNs from a JSON file."""
        try:
            with open("state.json", "r") as f:
                state = json.load(f)
                self.selected_crns = state.get("selected_crns", [])
                self.update_schedule()
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        """Handle window close event."""
        self.save_state()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    scheduler = CourseScheduler()
    scheduler.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
