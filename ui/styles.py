from PyQt5.QtWidgets import QApplication

ESTILO = """
QMainWindow {
    background-color: #f3f6f9;
}

QDialog {
    background-color: #ffffff;
}

QWidget {
    color: #1f2937;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #e2e8f0;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #ccfbf1;
    color: #134e4a;
}

QMenu::separator {
    height: 1px;
    background-color: #e2e8f0;
    margin: 4px 8px;
}

QTabWidget::pane {
    background-color: #ffffff;
    border: 1px solid #dbe2ea;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #e9eef3;
    color: #475569;
    border: 1px solid #dbe2ea;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 18px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0f766e;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #dde5ed;
}

QLineEdit,
QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 5px 8px;
    min-height: 22px;
    selection-background-color: #99f6e4;
    selection-color: #134e4a;
}

QLineEdit:focus,
QComboBox:focus {
    border: 1px solid #0f766e;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    selection-background-color: #ccfbf1;
    selection-color: #134e4a;
    outline: none;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 6px 12px;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton:disabled {
    background-color: #f8fafc;
    border-color: #e2e8f0;
    color: #94a3b8;
}

QPushButton#boton_primario {
    background-color: #0f766e;
    border-color: #0f766e;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#boton_primario:hover {
    background-color: #115e59;
    border-color: #115e59;
}

QPushButton#boton_primario:pressed {
    background-color: #134e4a;
    border-color: #134e4a;
}

QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #dbe2ea;
    border-radius: 4px;
    gridline-color: #e2e8f0;
    selection-background-color: #ccfbf1;
    selection-color: #134e4a;
    outline: none;
}

QTableView::item {
    padding: 4px 6px;
}

QTableView::item:selected {
    background-color: #ccfbf1;
    color: #134e4a;
}

QListWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #dbe2ea;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 4px 6px;
}

QListWidget::item:selected {
    background-color: #ccfbf1;
    color: #134e4a;
}

QHeaderView::section {
    background-color: #eef2f6;
    color: #334155;
    border: none;
    border-right: 1px solid #dbe2ea;
    border-bottom: 1px solid #dbe2ea;
    padding: 6px 7px;
    font-weight: 600;
}

QTableCornerButton::section {
    background-color: #eef2f6;
    border: none;
}

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #334155;
    font-weight: 600;
}

QFrame#tarjeta_estadistica {
    background-color: #ffffff;
    border: 1px solid #dbe2ea;
    border-radius: 8px;
}

QLabel#subtitulo {
    color: #64748b;
}

QLabel#estado_tabla {
    color: #475569;
    padding: 2px 0;
}

QLabel#titulo_tarjeta {
    color: #64748b;
    font-weight: 600;
}

QLabel#detalle_tarjeta {
    color: #475569;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e2e8f0;
    color: #475569;
}

QStatusBar QLabel {
    padding: 2px 8px;
}

QToolTip {
    background-color: #1f2937;
    color: #ffffff;
    border: 1px solid #111827;
    padding: 5px;
}
"""


def aplicar_estilo(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(ESTILO)
