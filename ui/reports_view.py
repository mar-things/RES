"""
RES - ui/reports_view.py
========================
Reports and KPI dashboard.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.report_service import (
    build_kpi_snapshot,
    export_csv,
    export_excel,
    export_pdf,
    process_variance_report,
    transit_time_report,
    vehicle_cost_report,
)


class ReportsView(QWidget):
    """Operational reports with KPI charts and export actions."""

    def __init__(self, parent=None) -> None:
        """Build the reports UI."""
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Create report controls, chart area, and data table."""
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(self.tr("Reports & KPI Analytics"))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton(self.tr("Refresh"))
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        csv_btn = QPushButton(self.tr("Export CSV"))
        csv_btn.clicked.connect(lambda: self._export("csv"))
        header.addWidget(csv_btn)

        xls_btn = QPushButton(self.tr("Export Excel"))
        xls_btn.clicked.connect(lambda: self._export("excel"))
        header.addWidget(xls_btn)

        pdf_btn = QPushButton(self.tr("Export PDF"))
        pdf_btn.clicked.connect(lambda: self._export("pdf"))
        header.addWidget(pdf_btn)
        root.addLayout(header)

        self._kpi_label = QLabel()
        self._kpi_label.setObjectName("subtitle")
        root.addWidget(self._kpi_label)

        self._chart_container = QWidget()
        self._chart_layout = QVBoxLayout(self._chart_container)
        self._chart_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._chart_container, stretch=1)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            self.tr("Section"),
            self.tr("Name"),
            self.tr("Metric A"),
            self.tr("Metric B"),
            self.tr("Metric C"),
        ])
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self._table, stretch=2)

    def refresh(self) -> None:
        """Reload report data."""
        snapshot = build_kpi_snapshot()
        self._kpi_label.setText(
            self.tr(
                "Active vehicles: {active} | Open findings: {findings} | "
                "Avg transit: {transit:.1f} min | Time variance: {variance:.1f} h | "
                "Actual cost: ${cost:.2f}"
            ).format(
                active=snapshot.active_vehicle_count,
                findings=snapshot.open_finding_count,
                transit=snapshot.average_transit_minutes,
                variance=snapshot.total_variance_hours,
                cost=snapshot.actual_cost_total,
            )
        )
        self._refresh_chart()
        self._refresh_table()

    def _refresh_chart(self) -> None:
        """Draw a variance chart using PyQtGraph when available."""
        while self._chart_layout.count():
            item = self._chart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        variances = process_variance_report()
        try:
            import pyqtgraph as pg

            plot = pg.PlotWidget()
            plot.setBackground("#1a1d23")
            plot.setTitle(self.tr("Actual vs Estimated Hours"))
            x_values = list(range(len(variances)))
            estimated = [row.estimated_hours for row in variances]
            actual = [row.actual_hours for row in variances]
            plot.plot(x_values, estimated, pen=pg.mkPen("#60a5fa", width=2), name="Estimated")
            plot.plot(x_values, actual, pen=pg.mkPen("#f59e0b", width=2), name="Actual")
            self._chart_layout.addWidget(plot)
        except Exception:
            self._chart_layout.addWidget(QLabel(self.tr("PyQtGraph chart unavailable.")))

    def _refresh_table(self) -> None:
        """Populate report rows."""
        rows: list[tuple[str, str, str, str, str]] = []
        for row in transit_time_report():
            rows.append((
                self.tr("Transit"),
                row.process_name,
                f"{row.transition_count}",
                f"{row.average_minutes:.1f} min",
                f"capacity {row.capacity_delay_count} / staff {row.staff_delay_count}",
            ))
        for row in process_variance_report():
            rows.append((
                self.tr("Time"),
                row.process_name,
                f"{row.completed_count} completed",
                f"est {row.estimated_hours:.1f}h",
                f"var {row.variance_hours:.1f}h",
            ))
        for row in vehicle_cost_report():
            rows.append((
                self.tr("Cost"),
                row.plate,
                f"findings ${row.findings_cost:.2f}",
                f"parts ${row.parts_cost:.2f}",
                f"total ${row.total_cost:.2f}",
            ))

        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                self._table.setItem(row_index, col_index, QTableWidgetItem(value))
        self._table.resizeColumnsToContents()

    def _export(self, kind: str) -> None:
        """Export reports to the selected format."""
        suffix = {"csv": "csv", "excel": "csv", "pdf": "pdf"}[kind]
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Report"),
            str(Path.cwd() / f"res_report.{suffix}"),
            self.tr("Report Files (*.{suffix})").format(suffix=suffix),
        )
        if not path:
            return
        try:
            if kind == "csv":
                written = export_csv(path)
            elif kind == "excel":
                written = export_excel(path)
            else:
                written = export_pdf(path)
            QMessageBox.information(self, self.tr("Export Complete"), str(written))
        except Exception as exc:
            QMessageBox.warning(self, self.tr("Export Failed"), str(exc))
