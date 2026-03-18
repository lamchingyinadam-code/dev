import sys
import json
import csv
import webbrowser
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
import duckdb
from requests.auth import HTTPBasicAuth

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QObject, QRunnable, QThreadPool, Signal, QDate, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QRadioButton,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
    QScrollArea,
    QComboBox,
    QSlider,
)

APP_TITLE = "Connect Mobility eFile API"
DEFAULT_BASE_URL = "https://api.connect.ihsmarkit.com/automotive/v1"
DEV_DEFAULT_USERNAME = "560e7557-c711-4bec-b0a8-561dd36c655b"
DEV_DEFAULT_PASSWORD = "LtTY6zwkHhq4vJ3n"
DEV_DEFAULT_TITLE = "SPGM_LV_Production_Base_Global_20"

STYLE = """
QWidget {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
    color: #111827;
    background: #f7f9fc;
}
QMainWindow {
    background: #f3f6fb;
}
QScrollArea, QAbstractScrollArea {
    border: none;
    background: transparent;
}
QToolBar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e6ebf2;
    spacing: 8px;
    padding: 6px 10px;
}
QStatusBar {
    background: #ffffff;
    color: #4b5563;
    border-top: 1px solid #e6ebf2;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #e7edf6;
    border-radius: 14px;
}
QGroupBox {
    font-weight: 600;
    margin-top: 10px;
    padding-top: 14px;
    background: #fbfcff;
    border: 1px solid #e7edf6;
    border-radius: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #334155;
}
QPushButton {
    background: #ffffff;
    color: #1f2937;
    border: 1px solid #d7e0ee;
    border-radius: 5px;
    padding: 8px 12px;
    font-weight: 600;
}
QPushButton:hover { border-color: #9cb4df; background: #f8fbff; }
QPushButton:pressed { background: #eef4ff; }
QPushButton:disabled {
    color: #9ca3af;
    background: #f3f4f6;
    border-color: #e5e7eb;
}
QPushButton#Primary {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #2563eb;
}
QPushButton#Primary:hover { background: #1d4ed8; border-color: #1d4ed8; }
QPushButton#Success {
    background: #059669;
    color: #ffffff;
    border: 1px solid #059669;
}
QPushButton#Success:hover { background: #047857; border-color: #047857; }
QPushButton#SectionToggle {
    background: transparent;
    border: none;
    padding: 0;
    text-align: left;
    color: #0f172a;
    font-size: 16pt;
    font-weight: 750;
}
QPushButton#SectionToggle:hover { color: #1d4ed8; }
QRadioButton {
    spacing: 8px;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #6b7280;
    background: #ffffff;
}
QRadioButton::indicator:checked {
    border: 2px solid #2563eb;
    background: #2563eb;
}
QRadioButton::indicator:unchecked {
    border: 2px solid #6b7280;
    background: #ffffff;
}
QLineEdit, QDateEdit, QComboBox, QListWidget, QTableView, QPlainTextEdit {
    background: #ffffff;
    color: #111827;
    border: 1px solid #d7e0ee;
    border-radius: 3px;
    padding: 6px;
    selection-background-color: #dbeafe;
    selection-color: #111827;
}
QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QListWidget:focus, QTableView:focus {
    border: 1px solid #7aa2e8;
}
QComboBox {
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #111827;
    border: 1px solid #d7e0ee;
    outline: 0;
    selection-background-color: #dbeafe;
    selection-color: #111827;
    show-decoration-selected: 0;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
}
QComboBox QAbstractItemView::indicator { width: 0px; height: 0px; }
QTableView {
    gridline-color: #eef2f7;
    alternate-background-color: #fafcff;
}
QTableView::item:selected,
QTableView::item:selected:!active {
    background: #dbeafe;
    color: #111827;
}
QHeaderView::section {
    background: #f5f8fd;
    color: #334155;
    border: none;
    border-bottom: 1px solid #e6ebf2;
    padding: 8px;
    font-weight: 700;
}
QListWidget::item {
    border-bottom: 1px solid #edf2f8;
    padding: 8px;
}
QListWidget::item:selected { background: #e8f0ff; }
QLabel[role="muted"] { color: #64748b; }
QLabel[role="summary"] {
    color: #475569;
    background: transparent;
    border: none;
    padding: 0;
}
QLabel[role="notice"], QLabel[role="good"], QLabel[role="warn"] {
    color: #1f2937;
    border: 1px solid #e6ebf2;
    border-radius: 10px;
    padding: 10px;
}
QLabel[role="notice"] { background: #f3f7ff; }
QLabel[role="good"] { background: #effcf5; }
QLabel[role="warn"] { background: #fffaf0; }
"""


@dataclass
class SettingsState:
    username: str = DEV_DEFAULT_USERNAME
    password: str = DEV_DEFAULT_PASSWORD
    base_url: str = DEFAULT_BASE_URL


@dataclass
class SearchState:
    title_mode: str = "contains"
    title_value: str = DEV_DEFAULT_TITLE
    published_to: date = field(default_factory=date.today)
    published_from_mode: str = ""  # "", relative, exact
    lookback_days: int = 120
    published_from_exact: date = field(default_factory=lambda: date.today() - timedelta(days=120))

    def effective_published_to(self) -> date:
        return self.published_to

    def effective_published_from(self) -> date:
        if self.published_from_mode == "relative":
            return self.published_to - timedelta(days=max(1, self.lookback_days))
        return self.published_from_exact


class RangeSlider(QWidget):
    valueChanged = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 100
        self._lower = 25
        self._upper = 75
        self._active = None  # 'lower' | 'upper'
        self._margin = 10
        self._groove_h = 4
        self._handle_r = 6
        self.setMinimumHeight(24)

    def setMinimum(self, v: int):
        self._minimum = int(v)
        if self._lower < self._minimum:
            self._lower = self._minimum
        if self._upper < self._lower:
            self._upper = self._lower
        self.update()

    def setMaximum(self, v: int):
        self._maximum = int(v)
        if self._upper > self._maximum:
            self._upper = self._maximum
        if self._lower > self._upper:
            self._lower = self._upper
        self.update()

    def lowerValue(self) -> int:
        return self._lower

    def upperValue(self) -> int:
        return self._upper

    def setValues(self, lo: int, hi: int):
        lo = max(self._minimum, min(int(lo), self._maximum))
        hi = max(self._minimum, min(int(hi), self._maximum))
        if lo > hi:
            lo, hi = hi, lo
        changed = (lo != self._lower) or (hi != self._upper)
        self._lower, self._upper = lo, hi
        self.update()
        if changed:
            self.valueChanged.emit(self._lower, self._upper)

    def _to_x(self, v: int) -> float:
        if self._maximum <= self._minimum:
            return float(self._margin)
        w = max(1, self.width() - 2 * self._margin)
        t = (v - self._minimum) / (self._maximum - self._minimum)
        return self._margin + t * w

    def _to_value(self, x: float) -> int:
        w = max(1, self.width() - 2 * self._margin)
        t = (x - self._margin) / w
        t = max(0.0, min(1.0, t))
        return int(round(self._minimum + t * (self._maximum - self._minimum)))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cy = self.height() / 2
        x1 = self._to_x(self._minimum)
        x2 = self._to_x(self._maximum)
        lx = self._to_x(self._lower)
        ux = self._to_x(self._upper)

        p.setPen(QPen(QColor("#d7e0ee"), self._groove_h))
        p.drawLine(int(x1), int(cy), int(x2), int(cy))

        p.setPen(QPen(QColor("#2563eb"), self._groove_h))
        p.drawLine(int(lx), int(cy), int(ux), int(cy))

        for x in (lx, ux):
            p.setPen(QPen(QColor("#1d4ed8"), 1))
            p.setBrush(QBrush(QColor("#ffffff")))
            p.drawEllipse(QRectF(x - self._handle_r, cy - self._handle_r, self._handle_r * 2, self._handle_r * 2))

    def mousePressEvent(self, e):
        x = e.position().x()
        lx = self._to_x(self._lower)
        ux = self._to_x(self._upper)
        self._active = 'lower' if abs(x - lx) <= abs(x - ux) else 'upper'
        self.mouseMoveEvent(e)

    def mouseMoveEvent(self, e):
        if not self._active:
            return
        v = self._to_value(e.position().x())
        if self._active == 'lower':
            self.setValues(v, self._upper)
        else:
            self.setValues(self._lower, v)

    def mouseReleaseEvent(self, _):
        self._active = None


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, rows: Optional[List[Dict[str, Any]]] = None, columns: Optional[List[str]] = None):
        super().__init__()
        self.rows = rows or []
        self.columns = columns or []
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder

    def set_data(self, rows: List[Dict[str, Any]], columns: List[str]):
        self.beginResetModel()
        self.rows = rows
        self.columns = columns
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def _is_date_header_col(self, col_name: str) -> bool:
        c = str(col_name or "").strip()
        return bool(
            re.fullmatch(r"([A-Z][a-z]{2})\s+\d{4}", c)
            or re.fullmatch(r"Q[1-4]\s+\d{4}", c)
            or re.fullmatch(r"CY\s?\d{4}", c)
        )

    def _format_with_commas_keep_decimals(self, value: Any) -> str:
        s = str(value)
        m = re.fullmatch(r"([+-]?)(\d+)(\.(\d+))?", s)
        if not m:
            return s
        sign = m.group(1) or ""
        int_part = m.group(2) or "0"
        frac_digits = m.group(4) or ""
        # Preserve original decimal precision unless it is pure trailing zeros (e.g. .0, .00)
        if frac_digits and set(frac_digits) == {"0"}:
            frac_full = ""
        else:
            frac_full = f".{frac_digits}" if frac_digits else ""
        int_with_commas = f"{int(int_part):,}"
        return f"{sign}{int_with_commas}{frac_full}"

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        col_name = self.columns[index.column()]
        row = self.rows[index.row()]
        value = row.get(col_name, "")
        if value is None:
            return ""

        if role == Qt.DisplayRole and self._is_date_header_col(col_name):
            return self._format_with_commas_keep_decimals(value)

        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return format(value, '.15g')
        return str(value)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        if column < 0 or column >= len(self.columns):
            return
        col = self.columns[column]

        def key_fn(r):
            v = r.get(col)
            if v is None:
                return (1, "")
            try:
                return (0, float(v))
            except Exception:
                return (0, str(v).lower())

        self.layoutAboutToBeChanged.emit()
        self.rows.sort(key=key_fn, reverse=(order == Qt.DescendingOrder))
        self._sort_column = column
        self._sort_order = order
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.columns[section] if section < len(self.columns) else ""
        return str(section + 1)


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)


class ApiWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class SettingsDialog(QDialog):
    def __init__(self, settings: SettingsState, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(560, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.username_edit = QLineEdit(settings.username)
        self.password_edit = QLineEdit(settings.password)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.base_url_edit = QLineEdit(settings.base_url)

        form.addRow("Username", self.username_edit)
        form.addRow("Password / PAT", self.password_edit)
        form.addRow("Base URL", self.base_url_edit)
        layout.addLayout(form)

        note = QLabel("Dev defaults are currently prefilled in this build and should be removed afterwards.")
        note.setProperty("role", "warn")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.save_btn = QPushButton("Confirm & Save")
        self.save_btn.setObjectName("Primary")
        buttons.addButton(self.save_btn, QDialogButtonBox.AcceptRole)
        buttons.rejected.connect(self.reject)
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(buttons)

    def get_settings(self) -> SettingsState:
        return SettingsState(
            username=self.username_edit.text().strip(),
            password=self.password_edit.text(),
            base_url=self.base_url_edit.text().strip() or DEFAULT_BASE_URL,
        )


class CollapsibleSection(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("Card")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 16, 18, 16)
        self.main_layout.setSpacing(12)

        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(10)
        self.title_btn = QPushButton(f"▸ {title}")
        self.title_btn.setObjectName("SectionToggle")
        self.title_btn.clicked.connect(self.toggle)
        self.header_layout.addWidget(self.title_btn)
        self.header_layout.addStretch(1)
        self.main_layout.addLayout(self.header_layout)

        self.summary_label = QLabel("")
        self.summary_label.setProperty("role", "summary")
        self.summary_label.setWordWrap(True)
        self.main_layout.addWidget(self.summary_label)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        self.main_layout.addWidget(self.content)

        self._title = title
        self._expanded = False
        self._toggle_handler = None
        self._sync_title()

    def _sync_title(self):
        self.title_btn.setText(("▾ " if self._expanded else "▸ ") + self._title)

    def set_toggle_handler(self, handler):
        self._toggle_handler = handler

    def toggle(self):
        if self._toggle_handler:
            self._toggle_handler()
        else:
            self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool):
        self._expanded = bool(expanded)
        self.content.setVisible(self._expanded)
        self._sync_title()

    def set_summary(self, text: str, show: bool = True):
        text = (text or "").strip()
        self.summary_label.setText(text)
        self.summary_label.setVisible(show and bool(text))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1500, 980)
        self.thread_pool = QThreadPool.globalInstance()

        self.settings = SettingsState()
        self.search = SearchState()
        self.fetch_all_pages = False
        self.fetch_pages = 1
        self.publications: List[str] = []
        self.filtered_publications: List[str] = []
        self.selected_publication: Optional[str] = None
        self.publication_confirmed = False
        self.search_confirmed = False
        self.efile_rows: List[Dict[str, Any]] = []
        self.selected_efile: Optional[Dict[str, Any]] = None
        self.efile_confirmed = False
        self.metadata_json: Any = None
        self.data_json: Any = None
        self.attachment_url: Optional[str] = None
        self.data_columns: List[str] = []
        self.data_rows: List[List[Any]] = []
        self.dataset_notice: str = ""
        self.query_date_meta: Dict[str, Dict[str, Any]] = {}
        self.query_date_columns: List[str] = []
        self.query_attr_columns: List[str] = []
        self.query_attr_selected: Dict[str, bool] = {}
        self.query_attr_filters: Dict[str, List[str]] = {}
        self.query_year_min: Optional[int] = None
        self.query_year_max: Optional[int] = None
        self.query_sort_column: Optional[str] = None
        self.query_sort_order: str = "ASC"
        self._extraction_tasks = 0
        self._extraction_errors: List[str] = []

        self._build_ui()
        self._apply_state_to_inputs()
        self.apply_theme_fixups()
        self.refresh_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel(APP_TITLE)
        title.setStyleSheet("font-size: 30pt; font-weight: 800;")
        top_row.addWidget(title)
        top_row.addStretch(1)
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("Primary")
        self.settings_btn.clicked.connect(self.open_settings)
        top_row.addWidget(self.settings_btn)
        outer.addLayout(top_row)

        self.status_note = QLabel("")
        self.status_note.setProperty("role", "notice")
        self.status_note.setVisible(False)
        self.status_note.setWordWrap(True)
        outer.addWidget(self.status_note)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)
        body = QWidget()
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(12)
        scroll.setWidget(body)

        self.search_section = self._build_search_section()
        self.efile_section = self._build_efile_section()
        self.dataset_section = self._build_dataset_section()

        for sec in [self.search_section, self.efile_section, self.dataset_section]:
            self.body_layout.addWidget(sec)
        self.body_layout.addStretch(1)

        self.setStatusBar(QStatusBar())

    def _build_publication_section(self):
        section = CollapsibleSection("Publication")
        section.set_summary("", show=False)
        section.set_expanded(False)
        section.set_toggle_handler(self.select_publication_clicked)

        section.inner_empty = QLabel("Loading publications…")
        section.inner_empty.setProperty("role", "muted")
        section.content_layout.addWidget(section.inner_empty)

        section.list_widget = QListWidget()
        section.list_widget.setMinimumHeight(220)
        section.list_widget.itemSelectionChanged.connect(self.on_publication_selected)
        section.content_layout.addWidget(section.list_widget)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        section.confirm_btn = QPushButton("Confirm Publication")
        section.confirm_btn.setObjectName("Primary")
        section.confirm_btn.clicked.connect(self.confirm_publication)
        bottom.addWidget(section.confirm_btn)
        section.content_layout.addLayout(bottom)
        return section

    def _build_search_section(self):
        section = CollapsibleSection("Define eFile Search")
        section.set_summary("", show=False)
        section.set_expanded(False)
        section.set_toggle_handler(self.on_search_section_toggled)

        # Publication (full-width)
        section.content_layout.addWidget(QLabel("Publication"))
        section.publication_combo = QComboBox()
        section.publication_combo.setMinimumHeight(27)
        section.publication_combo.setMaximumHeight(27)
        section.publication_combo.currentTextChanged.connect(self.on_publication_changed)
        section.content_layout.addWidget(section.publication_combo)

        # Title filter
        grid = QGridLayout()
        grid.addWidget(QLabel("Title"), 0, 0)
        title_row = QHBoxLayout()
        mode_row = QHBoxLayout()
        section.title_contains_radio = QRadioButton("contains")
        section.title_starts_radio = QRadioButton("starts with")
        section.title_ends_radio = QRadioButton("ends with")
        section.title_contains_radio.toggled.connect(self.sync_search_from_inputs)
        section.title_starts_radio.toggled.connect(self.sync_search_from_inputs)
        section.title_ends_radio.toggled.connect(self.sync_search_from_inputs)
        mode_row.addWidget(section.title_contains_radio)
        mode_row.addSpacing(20)
        mode_row.addWidget(section.title_starts_radio)
        mode_row.addSpacing(20)
        mode_row.addWidget(section.title_ends_radio)
        mode_row.addStretch(1)
        title_row.addLayout(mode_row, 1)
        section.title_value = QLineEdit()
        section.title_value.setMinimumHeight(27)
        section.title_value.setMaximumHeight(27)
        section.title_value.setPlaceholderText("Dataset title filter")
        section.title_value.textChanged.connect(self.sync_search_from_inputs)
        title_row.addWidget(section.title_value, 2)
        grid.addLayout(title_row, 1, 0, 1, 2)

        pub_to_box = QGroupBox("Published To Date")
        pub_to_layout = QGridLayout(pub_to_box)
        section.to_date = QDateEdit()
        section.to_date.setMinimumHeight(27)
        section.to_date.setMaximumHeight(27)
        section.to_date.setCalendarPopup(True)
        section.to_date.dateChanged.connect(self.on_published_to_changed)
        section.to_today_btn = QPushButton("Today")
        section.to_today_btn.clicked.connect(self.set_published_to_today)
        pub_to_layout.addWidget(QLabel("Date"), 0, 0)
        pub_to_layout.addWidget(section.to_date, 0, 1)
        pub_to_layout.addWidget(section.to_today_btn, 0, 2)

        pub_from_box = QGroupBox("Published From Date")
        pub_from_layout = QGridLayout(pub_from_box)
        radios_row = QHBoxLayout()
        section.from_relative_radio = QRadioButton("Relative Date")
        section.from_exact_radio = QRadioButton("Exact date")
        section.from_relative_radio.toggled.connect(self.sync_search_from_inputs)
        section.from_exact_radio.toggled.connect(self.sync_search_from_inputs)
        radios_row.addWidget(section.from_relative_radio)
        radios_row.addSpacing(20)
        radios_row.addWidget(section.from_exact_radio)
        radios_row.addStretch(1)
        pub_from_layout.addLayout(radios_row, 0, 0, 1, 2)

        section.lookback_row = QWidget()
        lookback_layout = QHBoxLayout(section.lookback_row)
        lookback_layout.setContentsMargins(0, 0, 0, 0)
        lookback_layout.setSpacing(6)
        section.lookback = QLineEdit("120")
        section.lookback.setMaximumWidth(80)
        section.lookback.textChanged.connect(self.sync_search_from_inputs)
        lookback_layout.addWidget(section.lookback)
        lookback_layout.addWidget(QLabel("days from Published To Date"))
        section.relative_date_label = QLabel("")
        section.relative_date_label.setProperty("role", "muted")
        section.relative_date_label.setStyleSheet("font-size: 9pt; color: #6b7280;")
        lookback_layout.addWidget(section.relative_date_label)
        lookback_layout.addStretch(1)

        section.from_date = QDateEdit()
        section.from_date.setMinimumHeight(27)
        section.from_date.setMaximumHeight(27)
        section.from_date.setCalendarPopup(True)
        section.from_date.dateChanged.connect(self.sync_search_from_inputs)

        pub_from_layout.addWidget(section.lookback_row, 1, 0, 1, 2)
        pub_from_layout.addWidget(section.from_date, 2, 0, 1, 2)

        fetch_box = QGroupBox("Load eFiles")
        fetch_layout = QVBoxLayout(fetch_box)

        fetch_mode_row = QHBoxLayout()
        section.fetch_pages_radio = QRadioButton("Pages")
        section.fetch_all_radio = QRadioButton("All")
        section.fetch_pages_radio.setAutoExclusive(False)
        section.fetch_all_radio.setAutoExclusive(False)
        section.fetch_pages_radio.toggled.connect(self.sync_search_from_inputs)
        section.fetch_all_radio.toggled.connect(self.sync_search_from_inputs)
        fetch_mode_row.addWidget(section.fetch_pages_radio)
        fetch_mode_row.addSpacing(20)
        fetch_mode_row.addWidget(section.fetch_all_radio)
        fetch_mode_row.addStretch(1)
        fetch_layout.addLayout(fetch_mode_row)

        section.pages_row = QWidget()
        pages_row_layout = QHBoxLayout(section.pages_row)
        pages_row_layout.setContentsMargins(0, 0, 0, 0)
        section.page_count = QLineEdit("1")
        section.page_count.setMinimumHeight(27)
        section.page_count.setMaximumHeight(27)
        section.page_count.setMaximumWidth(80)
        section.page_count.textChanged.connect(self.sync_search_from_inputs)
        pages_row_layout.addWidget(section.page_count)
        pages_row_layout.addWidget(QLabel("page(s)"))
        pages_row_layout.addStretch(1)
        fetch_layout.addWidget(section.pages_row)

        section.content_layout.addLayout(grid)
        side_by_side = QHBoxLayout()
        side_by_side.addWidget(pub_to_box, 1)
        side_by_side.addWidget(pub_from_box, 1)
        section.content_layout.addLayout(side_by_side)
        section.content_layout.addWidget(fetch_box)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        section.confirm_btn = QPushButton("Confirm")
        section.confirm_btn.setObjectName("Primary")
        section.confirm_btn.clicked.connect(self.confirm_search)
        bottom.addWidget(section.confirm_btn)
        section.content_layout.addLayout(bottom)
        return section

    def _build_efile_section(self):
        section = CollapsibleSection("Select eFile")
        section.set_summary("", show=False)
        section.set_expanded(False)
        section.set_toggle_handler(lambda: self.expand_only("efile"))

        section.count_label = QLabel("0 rows")
        section.count_label.setProperty("role", "muted")
        section.content_layout.addWidget(section.count_label)

        section.table_model = SimpleTableModel([], ["Id", "PublicationState", "PublishedOn", "Title", "UpdatedOn", "Download"])
        section.table = QTableView()
        section.table.setModel(section.table_model)
        section.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        section.table.setSelectionMode(QAbstractItemView.SingleSelection)
        section.table.setAlternatingRowColors(False)
        section.table.setMinimumHeight(260)
        section.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        section.table.horizontalHeader().setStretchLastSection(True)
        section.table.selectionModel().selectionChanged.connect(self.on_efile_selected)
        section.table.doubleClicked.connect(self.on_efile_table_double_clicked)
        section.content_layout.addWidget(section.table)

        button_row = QHBoxLayout()
        section.auto_btn = QPushButton("Select Latest")
        section.auto_btn.clicked.connect(self.select_latest_efile)
        button_row.addWidget(section.auto_btn)
        button_row.addStretch(1)
        section.confirm_btn = QPushButton("Extract Dataset")
        section.confirm_btn.setObjectName("Primary")
        section.confirm_btn.clicked.connect(self.confirm_efile)
        button_row.addWidget(section.confirm_btn)
        section.content_layout.addLayout(button_row)
        return section

    def _build_extract_section(self):
        section = CollapsibleSection("Extraction")
        section.set_summary("", show=False)
        section.set_expanded(False)

        opts_row = QHBoxLayout()
        section.link_cb = QCheckBox("Link")
        section.link_cb.setChecked(True)
        section.link_cb.stateChanged.connect(self.refresh_extract_preview)
        section.data_cb = QCheckBox("Data endpoint")
        section.data_cb.setChecked(True)
        section.data_cb.stateChanged.connect(self.refresh_extract_preview)
        opts_row.addWidget(section.link_cb)
        opts_row.addWidget(section.data_cb)
        opts_row.addStretch(1)
        section.content_layout.addLayout(opts_row)

        btn_row = QHBoxLayout()
        section.download_btn = QPushButton("Download eFile")
        section.download_btn.setObjectName("Success")
        section.download_btn.setEnabled(False)
        section.download_btn.clicked.connect(self.open_attachment_url)
        btn_row.addWidget(section.download_btn)
        btn_row.addStretch(1)
        section.run_btn = QPushButton("Run Extraction")
        section.run_btn.setObjectName("Primary")
        section.run_btn.clicked.connect(self.run_extraction)
        btn_row.addWidget(section.run_btn)
        section.content_layout.addLayout(btn_row)

        section.attachment_notice = QLabel("No metadata request has been run yet.")
        section.attachment_notice.setProperty("role", "notice")
        section.attachment_notice.setWordWrap(True)
        section.content_layout.addWidget(section.attachment_notice)

        section.data_notice = QLabel("No data request has been run yet.")
        section.data_notice.setProperty("role", "notice")
        section.data_notice.setWordWrap(True)
        section.content_layout.addWidget(section.data_notice)

        return section

    def _build_dataset_section(self):
        section = CollapsibleSection("Query")
        section.set_summary("", show=False)
        section.set_expanded(True)

        controls = QHBoxLayout()
        section.meta = QLabel("No dataset loaded")
        section.meta.setProperty("role", "muted")
        controls.addWidget(section.meta)
        controls.addStretch(1)
        section.export_btn = QPushButton("Export CSV")
        section.export_btn.clicked.connect(self.export_full_csv)
        controls.addWidget(section.export_btn)
        section.snippet_data_btn = QPushButton("Dataset Code")
        section.snippet_data_btn.clicked.connect(self.show_python_data_dialog)
        controls.addWidget(section.snippet_data_btn)
        section.snippet_download_btn = QPushButton("Download Link Code")
        section.snippet_download_btn.clicked.connect(self.show_python_download_dialog)
        controls.addWidget(section.snippet_download_btn)
        section.content_layout.addLayout(controls)

        section.notice = QLabel("")
        section.notice.setProperty("role", "warn")
        section.notice.setVisible(False)
        section.notice.setWordWrap(True)
        section.content_layout.addWidget(section.notice)

        # Query panel (shown only when date-like columns exist)
        section.query_wrap = QWidget()
        qh = QHBoxLayout(section.query_wrap)
        qh.setContentsMargins(0, 0, 0, 0)

        left = QFrame()
        left.setMinimumWidth(360)
        left.setMaximumWidth(440)
        left_l = QVBoxLayout(left)

        section.query_refresh_btn = QPushButton("Refresh")
        section.query_refresh_btn.setObjectName("Primary")
        section.query_refresh_btn.clicked.connect(self.on_query_refresh_clicked)
        left_l.addWidget(section.query_refresh_btn)

        year_box = QGroupBox("Years")
        yl = QVBoxLayout(year_box)
        row = QHBoxLayout()
        row.addWidget(QLabel("From"))
        section.year_from_label = QLabel("-")
        row.addWidget(section.year_from_label)
        row.addSpacing(10)
        section.year_range_slider = RangeSlider()
        section.year_range_slider.valueChanged.connect(lambda _lo, _hi: self._sync_year_labels())
        row.addWidget(section.year_range_slider, 1)
        row.addSpacing(10)
        row.addWidget(QLabel("To"))
        section.year_to_label = QLabel("-")
        row.addWidget(section.year_to_label)
        yl.addLayout(row)
        left_l.addWidget(year_box)

        gran_box = QGroupBox("Granularity")
        gl = QHBoxLayout(gran_box)
        section.g_yearly = QCheckBox("Yearly")
        section.g_quarterly = QCheckBox("Quarterly")
        section.g_monthly = QCheckBox("Monthly")
        gl.addWidget(section.g_yearly)
        gl.addWidget(section.g_quarterly)
        gl.addWidget(section.g_monthly)
        gl.addStretch(1)
        left_l.addWidget(gran_box)

        attr_title = QHBoxLayout()
        attr_title.addWidget(QLabel("Attributes"))
        attr_title.addStretch(1)
        section.attr_all_btn = QPushButton("Select All")
        section.attr_all_btn.clicked.connect(self.query_select_all_attrs)
        section.attr_none_btn = QPushButton("Deselect All")
        section.attr_none_btn.clicked.connect(self.query_deselect_all_attrs)
        attr_title.addWidget(section.attr_all_btn)
        attr_title.addWidget(section.attr_none_btn)
        left_l.addLayout(attr_title)

        section.attr_list = QListWidget()
        section.attr_list.setMinimumHeight(280)
        left_l.addWidget(section.attr_list, 1)

        right = QVBoxLayout()
        section.table_model = SimpleTableModel([], [])
        section.table = QTableView()
        section.table.setModel(section.table_model)
        section.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        section.table.setSortingEnabled(True)
        section.table.horizontalHeader().setSortIndicatorShown(True)
        section.table.horizontalHeader().sortIndicatorChanged.connect(self.on_query_sort_changed)
        section.table.setMinimumHeight(420)
        right.addWidget(section.table)

        qh.addWidget(left)
        qh.addLayout(right, 1)

        section.content_layout.addWidget(section.query_wrap)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch(1)
        section.query_code_btn = QPushButton("Query Code")
        section.query_code_btn.clicked.connect(self.show_python_query_dialog)
        bottom_row.addWidget(section.query_code_btn)
        section.content_layout.addLayout(bottom_row)

        section.query_wrap.setVisible(False)
        return section

    def apply_theme_fixups(self):
        # Force a deterministic light theme regardless of OS theme/palette.
        self.setStyleSheet(STYLE)

    def _apply_state_to_inputs(self):
        s = self.search_section
        s.title_contains_radio.setChecked(self.search.title_mode == "contains")
        s.title_starts_radio.setChecked(self.search.title_mode == "starts with")
        s.title_ends_radio.setChecked(self.search.title_mode == "ends with")
        s.title_value.setText(self.search.title_value)
        s.to_date.setDate(QDate(self.search.published_to.year, self.search.published_to.month, self.search.published_to.day))
        s.from_relative_radio.setChecked(self.search.published_from_mode == "relative")
        s.from_exact_radio.setChecked(self.search.published_from_mode == "exact")
        s.lookback.setText(str(self.search.lookback_days))
        s.from_date.setDate(QDate(self.search.published_from_exact.year, self.search.published_from_exact.month, self.search.published_from_exact.day))
        s.fetch_pages_radio.setChecked(False)
        s.fetch_all_radio.setChecked(False)
        s.page_count.setText("1")
        if not s.title_value.text().strip():
            s.title_value.setText(DEV_DEFAULT_TITLE)
            self.search.title_value = DEV_DEFAULT_TITLE
        self.sync_search_from_inputs()

    def show_note(self, text: str, role: str = "notice"):
        self.status_note.setText(text)
        self.status_note.setProperty("role", role)
        self.status_note.style().unpolish(self.status_note)
        self.status_note.style().polish(self.status_note)
        self.status_note.setVisible(True)

    def hide_note(self):
        self.status_note.setVisible(False)

    def set_busy(self, busy: bool, message: str = ""):
        for btn in [
            self.settings_btn,
            self.search_section.confirm_btn,
            self.search_section.to_today_btn,
            self.efile_section.confirm_btn,
            self.efile_section.auto_btn,
            self.dataset_section.export_btn,
            self.dataset_section.snippet_data_btn,
            self.dataset_section.snippet_download_btn,
        ]:
            btn.setEnabled(not busy)
        self.statusBar().showMessage(message if busy else message or "Ready")
        QApplication.processEvents()

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.settings = dialog.get_settings()
            self.refresh_ui()
            self.statusBar().showMessage("Settings saved", 4000)

    def reset_session(self):
        self.publications = []
        self.filtered_publications = []
        self.selected_publication = None
        self.publication_confirmed = False
        self.search_confirmed = False
        self.efile_rows = []
        self.selected_efile = None
        self.efile_confirmed = False
        self.metadata_json = None
        self.data_json = None
        self.attachment_url = None
        self.data_columns = []
        self.data_rows = []
        self.dataset_notice = ""
        self.search = SearchState()
        self._apply_state_to_inputs()
        self.refresh_ui()
        self.statusBar().showMessage("Session reset", 4000)

    def api_get(self, path: str, params: Optional[Dict[str, Any]] = None):
        url = self.settings.base_url.rstrip("/") + path
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(self.settings.username, self.settings.password),
            timeout=120,
        )
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return response.text

    def on_search_section_toggled(self):
        expand = not self.search_section.content.isVisible()
        self.search_section.set_expanded(expand)
        if expand and not self.publications:
            self.load_publications()

    def on_publication_changed(self, value: str):
        self.selected_publication = (value or "").strip() or None
        self.search_confirmed = False
        self.session_summaries()

    def set_published_to_today(self):
        today = date.today()
        self.search_section.to_date.setDate(QDate(today.year, today.month, today.day))
        self.on_published_to_changed()

    def on_published_to_changed(self):
        if self.search.published_from_mode == "relative":
            calc = self.search_section.to_date.date().toPython() - timedelta(days=max(1, self.search.lookback_days))
            self.search_section.from_date.setDate(QDate(calc.year, calc.month, calc.day))
        self.sync_search_from_inputs()

    def expand_only(self, section_name: str):
        self.search_section.set_expanded(section_name == "search")
        self.efile_section.set_expanded(section_name == "efile")

    def refresh_ui(self):
        self.session_summaries()
        self.refresh_search_preview()
        self.refresh_efile_summary()
        self.refresh_results_views()

        self.search_section.set_expanded(self.search_section.content.isVisible())
        self.efile_section.set_expanded(False if self.efile_confirmed and not self.efile_section.content.isVisible() else self.efile_section.content.isVisible())

    def session_summaries(self):
        to_date = self.search.effective_published_to().isoformat()
        from_date = self.search.effective_published_from().isoformat()
        title_mode = self.search.title_mode
        title_value = self.search.title_value or "—"
        search_summary = f"Title {title_mode}: {title_value}\nPublished To: {to_date}      Published From: {from_date}"
        self.search_section.set_summary(search_summary if self.search_confirmed else "", self.search_confirmed)

        if self.selected_efile:
            efile_summary = (
                f"{self.selected_efile.get('Title')} (id: {self.selected_efile.get('Id')})\n"
                f"Published On: {self.selected_efile.get('PublishedOn')}      Updated On: {self.selected_efile.get('UpdatedOn')}"
            )
        else:
            efile_summary = ""
        self.efile_section.set_summary(efile_summary, bool(efile_summary))

        # Keep Query header clean; row/column counts are shown inside query interface only.
        self.dataset_section.set_summary("", False)

    def refresh_publication_list(self):
        self.publication_section.list_widget.blockSignals(True)
        self.publication_section.list_widget.clear()
        self.publication_empty_state = not bool(self.publications)
        self.publication_section.inner_empty.setText("No publications loaded.")
        self.publication_section.inner_empty.setVisible(self.publication_empty_state)
        self.publication_section.list_widget.setVisible(bool(self.publications))
        for publication in self.publications:
            item = QListWidgetItem(publication)
            self.publication_section.list_widget.addItem(item)
            if publication == self.selected_publication:
                item.setSelected(True)
        self.publication_section.list_widget.blockSignals(False)

    def on_publication_selected(self):
        item = self.publication_section.list_widget.currentItem()
        self.selected_publication = item.text() if item else None
        self.publication_confirmed = False
        self.session_summaries()

    def confirm_publication(self):
        if not self.selected_publication:
            QMessageBox.warning(self, "No publication", "Choose a publication first.")
            return
        self.publication_confirmed = True
        self.publication_section.set_expanded(False)
        if not self.search_confirmed:
            self.search_section.set_expanded(True)
        self.statusBar().showMessage("Publication confirmed", 3000)
        self.refresh_ui()

    def sync_search_from_inputs(self):
        s = self.search_section
        if s.title_starts_radio.isChecked():
            self.search.title_mode = "starts with"
        elif s.title_ends_radio.isChecked():
            self.search.title_mode = "ends with"
        else:
            self.search.title_mode = "contains"
        typed_title = s.title_value.text().strip()
        if typed_title:
            self.search.title_value = typed_title
        elif not self.search.title_value:
            self.search.title_value = DEV_DEFAULT_TITLE
            s.title_value.setText(DEV_DEFAULT_TITLE)
        self.selected_publication = (s.publication_combo.currentText() or "").strip() or None

        qd = s.to_date.date()
        self.search.published_to = date(qd.year(), qd.month(), qd.day())

        if s.from_relative_radio.isChecked():
            self.search.published_from_mode = "relative"
        elif s.from_exact_radio.isChecked():
            self.search.published_from_mode = "exact"
        else:
            self.search.published_from_mode = ""
        try:
            self.search.lookback_days = max(1, int((s.lookback.text() or "120").strip()))
        except ValueError:
            self.search.lookback_days = 120
            s.lookback.setText("120")

        if self.search.published_from_mode == "relative":
            calc = self.search.published_to - timedelta(days=self.search.lookback_days)
            self.search.published_from_exact = calc
            s.from_date.setDate(QDate(calc.year, calc.month, calc.day))
            s.lookback_row.setVisible(True)
            s.relative_date_label.setVisible(True)
            s.relative_date_label.setText(calc.isoformat())
            s.from_date.setVisible(False)
        elif self.search.published_from_mode == "exact":
            fd = s.from_date.date()
            self.search.published_from_exact = date(fd.year(), fd.month(), fd.day())
            s.lookback_row.setVisible(False)
            s.relative_date_label.setVisible(False)
            s.from_date.setVisible(True)
        else:
            s.lookback_row.setVisible(False)
            s.relative_date_label.setVisible(False)
            s.from_date.setVisible(False)

        if not s.fetch_pages_radio.isChecked() and not s.fetch_all_radio.isChecked():
            self.fetch_all_pages = False
            self.fetch_pages = 1
            s.pages_row.setVisible(False)
        else:
            self.fetch_all_pages = s.fetch_all_radio.isChecked()
            if self.fetch_all_pages:
                self.fetch_pages = 1
                s.pages_row.setVisible(False)
            else:
                s.pages_row.setVisible(True)
                try:
                    self.fetch_pages = max(1, int((s.page_count.text() or "1").strip()))
                except ValueError:
                    self.fetch_pages = 1
                    s.page_count.setText("1")

        self.search_confirmed = False
        self.refresh_search_preview()
        self.session_summaries()

    def refresh_search_preview(self):
        payload = {
            "baseUrl": self.settings.base_url,
            "endpoint": "/efiles",
            "params": {
                "publication": self.selected_publication,
                "publishedFrom": self.search.effective_published_from().isoformat(),
                "publishedTo": self.search.effective_published_to().isoformat(),
                "orderBy": "PublishedOn",
                "order": "Asc",
            },
            "titleFilterMode": self.search.title_mode,
            "titleFilterValue": self.search.title_value,
        }
        text = json.dumps(payload, indent=2)
        if hasattr(self.search_section, 'preview'):
            self.search_section.preview.setPlainText(text)

    def _title_matches(self, title: str) -> bool:
        needle = (self.search.title_value or "").lower()
        hay = (title or "").lower()
        if not needle:
            return True
        if self.search.title_mode == "starts with":
            return hay.startswith(needle)
        if self.search.title_mode == "ends with":
            return hay.endswith(needle)
        return needle in hay

    def _load_efiles_paged(self, params: Dict[str, Any]):
        all_rows: List[Dict[str, Any]] = []
        seen_ids = set()

        # Pages mode: page=1 means only pageIndex=0; page=n means 0..n-1
        max_loops = 10**9 if self.fetch_all_pages else max(1, self.fetch_pages)
        page_index = 0

        while page_index < max_loops:
            page_params = dict(params)
            page_params["pageIndex"] = page_index
            payload = self.api_get("/efiles", page_params)
            rows = payload if isinstance(payload, list) else []
            if not rows:
                break

            new_count = 0
            for item in rows:
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get("Id") or item.get("id") or "")
                key = item_id or f"_row_{page_index}_{len(all_rows)}"
                if key in seen_ids:
                    continue
                seen_ids.add(key)
                all_rows.append(item)
                new_count += 1

            # For max/all mode: stop once page yields no new values
            if self.fetch_all_pages and new_count == 0:
                break

            # Also stop repeated-page condition in finite mode to avoid duplicates
            if (not self.fetch_all_pages) and new_count == 0:
                break

            page_index += 1

        return all_rows

    def confirm_search(self):
        if not self.selected_publication:
            QMessageBox.warning(self, "No publication", "Confirm a publication first.")
            return
        self.sync_search_from_inputs()
        self.search_confirmed = True
        self.set_busy(True, "Searching eFiles...")
        params = {
            "publication": self.selected_publication,
            "publishedFrom": self.search.effective_published_from().isoformat(),
            "publishedTo": self.search.effective_published_to().isoformat(),
            "orderBy": "UpdatedOn",
            "order": "Desc",
        }
        worker = ApiWorker(self._load_efiles_paged, params)
        worker.signals.finished.connect(self._on_search_loaded)
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_search_loaded(self, payload):
        rows = payload if isinstance(payload, list) else []
        mapped = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            attachments = item.get("Attachments") if isinstance(item.get("Attachments"), list) else []
            first_attachment = attachments[0] if attachments and isinstance(attachments[0], dict) else {}
            attachment_url = first_attachment.get("Url") if isinstance(first_attachment, dict) else ""
            row = {
                "Id": item.get("Id") or item.get("id") or "",
                "PublicationState": item.get("PublicationState") or item.get("publicationState") or "",
                "PublishedOn": item.get("PublishedOn") or item.get("publishedOn") or "",
                "Title": item.get("Title") or item.get("title") or "",
                "UpdatedOn": item.get("UpdatedOn") or item.get("updatedOn") or "",
                "AttachmentUrl": attachment_url,
                "Download": "Open" if attachment_url else "",
            }
            if self._title_matches(str(row.get("Title", ""))):
                mapped.append(row)

        mapped = sorted(mapped, key=lambda r: str(r.get("UpdatedOn") or r.get("PublishedOn") or ""), reverse=True)

        prev_selected_id = str(self.selected_efile.get("Id")) if self.selected_efile else None
        self.efile_rows = mapped

        kept = None
        if prev_selected_id:
            kept = next((r for r in mapped if str(r.get("Id")) == prev_selected_id), None)

        self.selected_efile = kept
        self.attachment_url = kept.get("AttachmentUrl") if kept else None
        self.efile_confirmed = bool(kept and self.efile_confirmed)

        self.search_section.set_expanded(False)
        if not self.efile_confirmed:
            self.efile_section.set_expanded(True)
        self.refresh_ui()
        self.set_busy(False, f"Search returned {len(mapped)} matching eFile row(s)")

    def refresh_efile_summary(self):
        self.efile_section.count_label.setText(f"{len(self.efile_rows)} rows")
        self.efile_section.table_model.set_data(self.efile_rows, ["Id", "PublicationState", "PublishedOn", "Title", "UpdatedOn", "Download"])
        selection_model = self.efile_section.table.selectionModel()
        if not self.selected_efile:
            if selection_model is not None:
                selection_model.blockSignals(True)
                self.efile_section.table.clearSelection()
                selection_model.blockSignals(False)
            return
        try:
            idx = next(i for i, r in enumerate(self.efile_rows) if str(r.get("Id")) == str(self.selected_efile.get("Id")))
        except StopIteration:
            return
        if selection_model is None:
            return
        current_rows = selection_model.selectedRows()
        current_row = current_rows[0].row() if current_rows else None
        if current_row == idx:
            return
        selection_model.blockSignals(True)
        self.efile_section.table.selectRow(idx)
        selection_model.blockSignals(False)

    def on_efile_selected(self):
        idxs = self.efile_section.table.selectionModel().selectedRows()
        if not idxs:
            return
        row = idxs[0].row()
        if 0 <= row < len(self.efile_rows):
            selected = dict(self.efile_rows[row])
            if self.selected_efile and str(self.selected_efile.get("Id")) == str(selected.get("Id")):
                return
            self.selected_efile = selected
            self.attachment_url = selected.get("AttachmentUrl")
            self.efile_confirmed = False
            self.session_summaries()

    def on_efile_table_double_clicked(self, index):
        if not index.isValid():
            return
        col = self.efile_section.table_model.columns[index.column()]
        if col != "Download":
            return
        row = self.efile_rows[index.row()] if 0 <= index.row() < len(self.efile_rows) else None
        if row and row.get("AttachmentUrl"):
            webbrowser.open(str(row.get("AttachmentUrl")))

    def select_latest_efile(self):
        if not self.efile_rows:
            return
        self.selected_efile = sorted(self.efile_rows, key=lambda r: str(r.get("UpdatedOn") or ""), reverse=True)[0]
        self.attachment_url = self.selected_efile.get("AttachmentUrl")
        self.refresh_ui()
        self.statusBar().showMessage(f"Auto-selected latest eFile: {self.selected_efile.get('Id')}", 4000)

    def confirm_efile(self):
        if not self.selected_efile:
            QMessageBox.warning(self, "No eFile", "Select an eFile row first.")
            return
        self.efile_confirmed = True
        self.efile_section.set_expanded(False)
        self.dataset_section.set_expanded(True)
        self.statusBar().showMessage("eFile confirmed — loading dataset...", 3000)

        self.data_json = None
        self.data_columns = []
        self.data_rows = []
        self.dataset_notice = ""
        self.refresh_results_views()
        self.set_busy(True, "Loading dataset...")
        worker = ApiWorker(self.api_get, f"/efiles/{self.selected_efile.get('Id')}/data")
        worker.signals.finished.connect(self._on_data_finished)
        worker.signals.error.connect(self._on_dataset_load_error)
        self.thread_pool.start(worker)

    def refresh_extract_preview(self):
        # Kept for state refresh hooks; no raw JSON preview shown in UI.
        return

    def run_extraction(self):
        if not self.selected_efile:
            QMessageBox.warning(self, "No eFile", "Select an eFile first.")
            return
        if not self.extract_section.link_cb.isChecked() and not self.extract_section.data_cb.isChecked():
            QMessageBox.warning(self, "No extraction option", "Choose at least one extraction option.")
            return
        self.metadata_json = None
        self.data_json = None
        self.attachment_url = None
        self.data_columns = []
        self.data_rows = []
        self.refresh_results_views()
        self.set_busy(True, "Running extraction...")
        self._extraction_tasks = int(self.extract_section.link_cb.isChecked()) + int(self.extract_section.data_cb.isChecked())
        self._extraction_errors = []

        if self.extract_section.link_cb.isChecked():
            worker = ApiWorker(self.api_get, f"/efiles/{self.selected_efile.get('Id')}")
            worker.signals.finished.connect(self._on_meta_finished)
            worker.signals.error.connect(self._on_meta_error)
            self.thread_pool.start(worker)

        if self.extract_section.data_cb.isChecked():
            worker = ApiWorker(self.api_get, f"/efiles/{self.selected_efile.get('Id')}/data")
            worker.signals.finished.connect(self._on_data_finished)
            worker.signals.error.connect(self._on_data_error)
            self.thread_pool.start(worker)

    def _on_meta_finished(self, payload):
        self.metadata_json = payload
        url = None
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            attachments = payload[0].get("Attachments") or []
            if attachments and isinstance(attachments[0], dict):
                url = attachments[0].get("Url")
        elif isinstance(payload, dict):
            attachments = payload.get("Attachments") or []
            if attachments and isinstance(attachments[0], dict):
                url = attachments[0].get("Url")
        self.attachment_url = url
        self._check_extraction_done()

    def _on_meta_error(self, msg):
        self._extraction_errors.append(f"Metadata request failed: {msg}")
        self._check_extraction_done()

    def _on_data_finished(self, payload):
        self.data_json = payload
        if isinstance(payload, dict) and isinstance(payload.get("ColumnNames"), list) and isinstance(payload.get("Data"), list):
            self.data_columns = payload["ColumnNames"]
            self.data_rows = payload["Data"]
            self.dataset_notice = ""
        else:
            self.dataset_notice = "This dataset does not have callable data tables, please use the download link in Select eFile instead."
        self.set_busy(False, "Dataset loaded")
        self.refresh_ui()

    def _on_dataset_load_error(self, msg):
        if "404" in str(msg):
            self.dataset_notice = "This dataset does not have callable data tables, please use the download link in Select eFile instead."
            self.set_busy(False, "Dataset not callable")
            self.refresh_ui()
            return
        self.set_busy(False, "Dataset request failed")
        QMessageBox.critical(self, "Dataset error", str(msg))

    def _on_data_error(self, msg):
        self._extraction_errors.append(f"Data request failed: {msg}")
        self._check_extraction_done()

    def _check_extraction_done(self):
        self._extraction_tasks -= 1
        if self._extraction_tasks <= 0:
            self.set_busy(False, "Extraction completed" if not self._extraction_errors else "Extraction completed with issues")
            if self._extraction_errors:
                QMessageBox.warning(self, "Extraction issues", "\n\n".join(self._extraction_errors))
            self.refresh_ui()

    def _classify_date_column(self, col: str):
        m = re.fullmatch(r"([A-Z][a-z]{2})\s+(\d{4})", str(col).strip())
        if m:
            return {"kind": "monthly", "year": int(m.group(2)), "sort": (int(m.group(2)), 3, m.group(1))}
        m = re.fullmatch(r"Q([1-4])\s+(\d{4})", str(col).strip())
        if m:
            return {"kind": "quarterly", "year": int(m.group(2)), "sort": (int(m.group(2)), 2, int(m.group(1)))}
        m = re.fullmatch(r"CY\s?(\d{4})", str(col).strip())
        if m:
            return {"kind": "yearly", "year": int(m.group(1)), "sort": (int(m.group(1)), 1, 0)}
        return None

    def _init_query_from_dataset(self):
        self.query_date_meta = {}
        for c in self.data_columns:
            meta = self._classify_date_column(c)
            if meta:
                self.query_date_meta[c] = meta
        self.query_date_columns = sorted(self.query_date_meta.keys(), key=lambda c: self.query_date_meta[c]["sort"])
        self.query_attr_columns = [c for c in self.data_columns if c not in self.query_date_meta]

        years = sorted({self.query_date_meta[c]["year"] for c in self.query_date_columns})
        self.query_year_min = years[0] if years else None
        self.query_year_max = years[-1] if years else None

        self.query_attr_selected = {c: True for c in self.query_attr_columns}
        self.query_attr_filters = {c: [] for c in self.query_attr_columns}
        self.query_sort_column = None
        self.query_sort_order = "ASC"

        s = self.dataset_section
        has_query = bool(self.query_date_columns)
        s.query_wrap.setVisible(has_query)
        if not has_query:
            return

        s.g_yearly.setChecked(True)
        s.g_quarterly.setChecked(True)
        s.g_monthly.setChecked(True)

        s.year_range_slider.setMinimum(self.query_year_min)
        s.year_range_slider.setMaximum(self.query_year_max)
        s.year_range_slider.setValues(self.query_year_min, self.query_year_max)
        self._sync_year_labels()
        self._rebuild_attribute_rows()

    def _sync_year_labels(self):
        if self.query_year_min is None:
            return
        s = self.dataset_section
        lo = s.year_range_slider.lowerValue()
        hi = s.year_range_slider.upperValue()
        s.year_from_label.setText(str(lo))
        s.year_to_label.setText(str(hi))

    def _rebuild_attribute_rows(self):
        s = self.dataset_section
        s.attr_list.clear()
        for col in self.query_attr_columns:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(4, 2, 4, 2)
            cb = QCheckBox(col)
            cb.setChecked(self.query_attr_selected.get(col, True))
            cb.stateChanged.connect(lambda _=None, c=col, box=cb: self._on_attr_checked(c, box.isChecked()))
            h.addWidget(cb, 1)
            fbtn = QPushButton("⛃")
            fbtn.setMaximumWidth(30)
            fbtn.clicked.connect(lambda _=None, c=col: self._open_attr_filter(c))
            h.addWidget(fbtn)
            item = QListWidgetItem()
            hint = row.sizeHint()
            hint.setHeight(max(hint.height(), 32))
            item.setSizeHint(hint)
            s.attr_list.addItem(item)
            s.attr_list.setItemWidget(item, row)

    def _on_attr_checked(self, col: str, checked: bool):
        self.query_attr_selected[col] = checked

    def _open_attr_filter(self, col: str):
        if not self.data_columns or col not in self.data_columns:
            return
        idx = self.data_columns.index(col)
        vals = []
        for r in self.data_rows:
            v = r[idx] if idx < len(r) else None
            vals.append("(blank)" if v is None or str(v)=="" else str(v))
        uniq = sorted(set(vals))

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Filter: {col}")
        dlg.resize(420, 520)
        l = QVBoxLayout(dlg)
        search = QLineEdit()
        search.setPlaceholderText("Search values")
        l.addWidget(search)
        lw = QListWidget()
        l.addWidget(lw, 1)

        selected = set(self.query_attr_filters.get(col, []))
        if not selected:
            selected = set(uniq)

        def reload_list():
            q = search.text().lower().strip()
            lw.clear()
            for v in uniq:
                if q and q not in v.lower():
                    continue
                it = QListWidgetItem(v)
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Checked if v in selected else Qt.Unchecked)
                lw.addItem(it)

        def on_change(item):
            v = item.text()
            if item.checkState() == Qt.Checked:
                selected.add(v)
            else:
                selected.discard(v)

        lw.itemChanged.connect(on_change)
        search.textChanged.connect(lambda _: reload_list())
        reload_list()

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        l.addWidget(btns)
        if dlg.exec() == QDialog.Accepted:
            # if everything selected, store empty (no-op filter)
            self.query_attr_filters[col] = [] if len(selected) == len(uniq) else sorted(selected)

    def query_select_all_attrs(self):
        for c in self.query_attr_columns:
            self.query_attr_selected[c] = True
        self._rebuild_attribute_rows()

    def query_deselect_all_attrs(self):
        for c in self.query_attr_columns:
            self.query_attr_selected[c] = False
        self._rebuild_attribute_rows()

    def on_query_refresh_clicked(self):
        self._refresh_query_table()

    def on_query_sort_changed(self, logical_index: int, order: Qt.SortOrder):
        cols = self.dataset_section.table_model.columns
        if 0 <= logical_index < len(cols):
            self.query_sort_column = cols[logical_index]
            self.query_sort_order = "DESC" if order == Qt.DescendingOrder else "ASC"

    def _refresh_query_table(self):
        if not self.data_columns:
            return
        if not self.query_date_columns:
            # fallback full dataset
            full_rows = [dict(zip(self.data_columns, row)) for row in self.data_rows]
            self.dataset_section.table_model.set_data(full_rows, self.data_columns)
            if self.query_sort_column and self.query_sort_column in self.data_columns:
                cidx = self.data_columns.index(self.query_sort_column)
                order = Qt.DescendingOrder if self.query_sort_order == "DESC" else Qt.AscendingOrder
                self.dataset_section.table.sortByColumn(cidx, order)
            return

        s = self.dataset_section
        lo = s.year_range_slider.lowerValue()
        hi = s.year_range_slider.upperValue()
        kinds = set()
        if s.g_yearly.isChecked(): kinds.add('yearly')
        if s.g_quarterly.isChecked(): kinds.add('quarterly')
        if s.g_monthly.isChecked(): kinds.add('monthly')
        if not kinds:
            kinds = {'yearly','quarterly','monthly'}

        chosen_dates = [c for c in self.query_date_columns if lo <= self.query_date_meta[c]['year'] <= hi and self.query_date_meta[c]['kind'] in kinds]
        group_cols = [c for c in self.query_attr_columns if self.query_attr_selected.get(c, True)]

        df = pd.DataFrame(self.data_rows, columns=self.data_columns)

        # apply value filters (AND across cols, OR within)
        for col in self.query_attr_columns:
            picks = self.query_attr_filters.get(col, [])
            if not picks:
                continue
            ser = df[col].astype(str)
            is_blank = df[col].isna() | (ser == "")
            mask = ser.isin([v for v in picks if v != '(blank)'])
            if '(blank)' in picks:
                mask = mask | is_blank
            df = df[mask]

        # coerce date cols numeric
        for c in chosen_dates:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        if chosen_dates:
            con = duckdb.connect(':memory:')
            con.register('t', df)
            sel = []
            if group_cols:
                sel.extend([f'"{c}"' for c in group_cols])
            sel.extend([f'SUM("{c}") AS "{c}"' for c in chosen_dates])
            if not sel:
                sel = [f'SUM("{c}") AS "{c}"' for c in chosen_dates]
            sql = f"SELECT {', '.join(sel)} FROM t"
            if group_cols:
                sql += " GROUP BY " + ", ".join([f'"{c}"' for c in group_cols])
            out = con.execute(sql).df()
        else:
            out = df[group_cols].drop_duplicates() if group_cols else pd.DataFrame([{}])

        rows = out.to_dict(orient='records')
        cols = list(out.columns)
        self.dataset_section.table_model.set_data(rows, cols)
        if self.query_sort_column and self.query_sort_column in cols:
            cidx = cols.index(self.query_sort_column)
            order = Qt.DescendingOrder if self.query_sort_order == "DESC" else Qt.AscendingOrder
            self.dataset_section.table.sortByColumn(cidx, order)

    def refresh_results_views(self):
        self.dataset_section.meta.setText(
            "No dataset loaded" if not self.data_columns else f"{len(self.data_rows)} rows × {len(self.data_columns)} columns"
        )
        self.dataset_section.export_btn.setEnabled(bool(self.data_columns))

        notice_text = (self.dataset_notice or "").strip()
        self.dataset_section.notice.setText(notice_text)
        self.dataset_section.notice.setVisible(bool(notice_text))

        if self.data_columns:
            self._init_query_from_dataset()
            self._refresh_query_table()
        else:
            self.dataset_section.query_wrap.setVisible(False)
            self.dataset_section.table_model.set_data([], [])

    def open_attachment_url(self):
        if self.attachment_url:
            webbrowser.open(self.attachment_url)

    def export_full_csv(self):
        model = self.dataset_section.table_model
        cols = list(model.columns)
        rows = list(model.rows)
        if not cols:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            f"efile_view_{self.selected_efile.get('Id') if self.selected_efile else 'data'}.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for r in rows:
                writer.writerow([r.get(c, "") for c in cols])
        self.statusBar().showMessage(f"Saved current table view to {path}", 5000)

    def _show_code_dialog(self, title: str, code: str):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(980, 720)
        layout = QVBoxLayout(dlg)
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setPlainText(code)
        layout.addWidget(editor)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("Primary")

        def _copy():
            QApplication.clipboard().setText(code)
            self.statusBar().showMessage("Python code copied", 3000)

        copy_btn.clicked.connect(_copy)
        buttons.addButton(copy_btn, QDialogButtonBox.ActionRole)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        dlg.exec()

    def build_python_data_snippet(self) -> str:
        publication = self.selected_publication or ""
        title_value = self.search.title_value or ""
        published_to = self.search.effective_published_to().isoformat()
        published_from = self.search.effective_published_from().isoformat()
        efile_id = self.selected_efile.get("Id") if self.selected_efile else ""
        title_mode = self.search.title_mode
        mode_expr = {
            "contains": f"df['Title'].astype(str).str.contains({title_value!r}, na=False)",
            "starts with": f"df['Title'].astype(str).str.startswith({title_value!r}, na=False)",
            "ends with": f"df['Title'].astype(str).str.endswith({title_value!r}, na=False)",
        }.get(title_mode, f"df['Title'].astype(str).str.contains({title_value!r}, na=False)")

        all_pages = self.fetch_all_pages
        max_pages = self.fetch_pages
        return f'''import base64
import pandas as pd
import requests
import pandas as pd
import duckdb

username = {self.settings.username!r}
password = {self.settings.password!r}
encoded_token = base64.b64encode(f"{{username}}:{{password}}".encode()).decode()
headers = {{"Authorization": f"Basic {{encoded_token}}"}}
BASE = {self.settings.base_url!r}

all_pages = {all_pages}
max_pages = {max_pages}

params = {{
    "publication": {publication!r},
    "publishedFrom": {published_from!r},
    "publishedTo": {published_to!r},
    "orderBy": "UpdatedOn",
    "order": "Desc",
}}

rows = []
page = 1
while True:
    page_params = dict(params)
    page_params["pageIndex"] = page
    resp = requests.get(f"{{BASE}}/efiles", headers=headers, params=page_params)
    resp.raise_for_status()
    batch = resp.json() if isinstance(resp.json(), list) else []
    if not batch:
        break
    rows.extend(batch)
    if not all_pages and page >= max_pages:
        break
    page += 1

df = pd.DataFrame(rows)[["Id", "PublicationState", "PublishedOn", "Title", "UpdatedOn"]] if rows else pd.DataFrame(columns=["Id", "PublicationState", "PublishedOn", "Title", "UpdatedOn"])
df = df.loc[{mode_expr}]

id_value = {efile_id!r} or (df.iloc[-1]["Id"] if not df.empty else None)
if id_value is None:
    raise RuntimeError("No eFile found for the selected filters")

r = requests.get(f"{{BASE}}/efiles/{{id_value}}/data", headers=headers)
if r.ok:
    payload = r.json()
    df_data = pd.DataFrame(payload.get("Data", []), columns=payload.get("ColumnNames", []))
    print(df_data)
else:
    print(f"Data request failed: {{r.status_code}}\\n{{r.text}}")
'''

    def build_python_download_snippet(self) -> str:
        publication = self.selected_publication or ""
        title_value = self.search.title_value or ""
        published_to = self.search.effective_published_to().isoformat()
        published_from = self.search.effective_published_from().isoformat()
        efile_id = self.selected_efile.get("Id") if self.selected_efile else ""
        title_mode = self.search.title_mode
        mode_expr = {
            "contains": f"df['Title'].astype(str).str.contains({title_value!r}, na=False)",
            "starts with": f"df['Title'].astype(str).str.startswith({title_value!r}, na=False)",
            "ends with": f"df['Title'].astype(str).str.endswith({title_value!r}, na=False)",
        }.get(title_mode, f"df['Title'].astype(str).str.contains({title_value!r}, na=False)")

        all_pages = self.fetch_all_pages
        max_pages = self.fetch_pages
        return f'''import base64
import webbrowser
import re
import pandas as pd
import requests
import pandas as pd
import duckdb

username = {self.settings.username!r}
password = {self.settings.password!r}
encoded_token = base64.b64encode(f"{{username}}:{{password}}".encode()).decode()
headers = {{"Authorization": f"Basic {{encoded_token}}"}}
BASE = {self.settings.base_url!r}

all_pages = {all_pages}
max_pages = {max_pages}

params = {{
    "publication": {publication!r},
    "publishedFrom": {published_from!r},
    "publishedTo": {published_to!r},
    "orderBy": "UpdatedOn",
    "order": "Desc",
}}

rows = []
page = 1
while True:
    page_params = dict(params)
    page_params["pageIndex"] = page
    resp = requests.get(f"{{BASE}}/efiles", headers=headers, params=page_params)
    resp.raise_for_status()
    batch = resp.json() if isinstance(resp.json(), list) else []
    if not batch:
        break
    rows.extend(batch)
    if not all_pages and page >= max_pages:
        break
    page += 1

df = pd.DataFrame(rows)
if not df.empty:
    df = df.loc[{mode_expr}]

id_value = {efile_id!r} or (df.iloc[-1]["Id"] if not df.empty else None)
if id_value is None:
    raise RuntimeError("No eFile found for the selected filters")

row = df.loc[df["Id"] == id_value].iloc[0] if "Id" in df.columns and (df["Id"] == id_value).any() else None
attachment_url = ""
if row is not None:
    attachments = row.get("Attachments") or []
    if attachments and isinstance(attachments[0], dict):
        attachment_url = attachments[0].get("Url", "")

print("Download URL:", attachment_url)
if attachment_url:
    webbrowser.open(attachment_url)
'''

    def show_python_data_dialog(self):
        self._show_code_dialog("Python Code - Dataset", self.build_python_data_snippet())

    def build_python_query_snippet(self) -> str:
        base = self.build_python_data_snippet().rstrip()

        year_from = self.dataset_section.year_range_slider.lowerValue() if self.query_year_min is not None else None
        year_to = self.dataset_section.year_range_slider.upperValue() if self.query_year_max is not None else None

        granularities = []
        if self.dataset_section.g_yearly.isChecked():
            granularities.append("yearly")
        if self.dataset_section.g_quarterly.isChecked():
            granularities.append("quarterly")
        if self.dataset_section.g_monthly.isChecked():
            granularities.append("monthly")
        if not granularities:
            granularities = ["yearly", "quarterly", "monthly"]

        chosen_dates = [
            c for c in self.query_date_columns
            if year_from is not None and year_to is not None
            and year_from <= self.query_date_meta[c]['year'] <= year_to
            and self.query_date_meta[c]['kind'] in granularities
        ]
        group_cols = [c for c in self.query_attr_columns if self.query_attr_selected.get(c, True)]
        attr_filters = {k: v for k, v in self.query_attr_filters.items() if v}
        sort_col = self.query_sort_column
        sort_order = self.query_sort_order or "ASC"

        def qident(name: str) -> str:
            return '"' + str(name).replace('"', '""') + '"'

        def qstr(s: str) -> str:
            return "'" + str(s).replace("'", "''") + "'"

        where_clauses = []
        for col, picks in attr_filters.items():
            quoted_col = qident(col)
            non_blank = [p for p in picks if p != '(blank)']
            includes_blank = '(blank)' in picks
            sub = []
            if non_blank:
                vals = ", ".join(qstr(v) for v in non_blank)
                sub.append(f"CAST({quoted_col} AS VARCHAR) IN ({vals})")
            if includes_blank:
                sub.append(f"{quoted_col} IS NULL OR CAST({quoted_col} AS VARCHAR) = ''")
            if sub:
                where_clauses.append("(" + " OR ".join(sub) + ")")

        select_parts = [qident(c) for c in group_cols] + [f"SUM(COALESCE(TRY_CAST({qident(c)} AS DOUBLE), 0)) AS {qident(c)}" for c in chosen_dates]
        if not select_parts:
            select_parts = ["1 AS one"]

        group_by_sql = ""
        if group_cols:
            group_by_sql = "\nGROUP BY " + ", ".join(qident(c) for c in group_cols)

        order_by_sql = ""
        if sort_col:
            order_by_sql = f"\nORDER BY {qident(sort_col)} {sort_order}"

        where_sql = ""
        if where_clauses:
            where_sql = "\nWHERE " + "\n  AND ".join(where_clauses)

        sql = f"""WITH filtered AS (
    SELECT *
    FROM t{where_sql}
), aggregated AS (
    SELECT
        {", ".join(select_parts)}
    FROM filtered{group_by_sql}
)
SELECT *
FROM aggregated{order_by_sql};"""

        return base + f'''

# ------------------------
# Query section extension
# ------------------------
# Standalone replay of the exact current Query snapshot.
con = duckdb.connect(':memory:')
con.register('t', df_data)

sql = """{sql}"""
result_df = con.execute(sql).df()
print(sql)
print(result_df.head(50))
'''

    def show_python_query_dialog(self):
        self._show_code_dialog("Python Code - Query", self.build_python_query_snippet())

    def show_python_download_dialog(self):
        self._show_code_dialog("Python Code - Download Link", self.build_python_download_snippet())

    def load_publications(self):
        if not (self.settings.username and self.settings.password and self.settings.base_url):
            QMessageBox.warning(self, "Missing settings", "Username, password/PAT, and base URL are all required.")
            return
        self.set_busy(True, "Loading publications...")
        worker = ApiWorker(self.api_get, "/efiles/publication")
        worker.signals.finished.connect(self._on_publications_loaded)
        worker.signals.error.connect(self._on_api_error)
        self.thread_pool.start(worker)

    def _on_publications_loaded(self, payload):
        pubs = []
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, str):
                    pubs.append(item)
                elif isinstance(item, dict) and "Publication" in item:
                    pubs.append(str(item["Publication"]))
                else:
                    pubs.append(str(item))
        self.publications = [p for p in pubs if p]

        combo = self.search_section.publication_combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(self.publications)
        if self.selected_publication and self.selected_publication in self.publications:
            combo.setCurrentText(self.selected_publication)
        elif self.publications:
            combo.setCurrentIndex(0)
            self.selected_publication = combo.currentText()
        combo.blockSignals(False)

        self.refresh_ui()
        self.set_busy(False, f"Loaded {len(self.publications)} publications")

    def _on_api_error(self, message: str):
        self.set_busy(False, "Request failed")
        QMessageBox.critical(self, "API error", message)


def main():
    app = QApplication(sys.argv)
    # Fusion style is more consistent for custom radio indicators across platforms (incl. Windows).
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
