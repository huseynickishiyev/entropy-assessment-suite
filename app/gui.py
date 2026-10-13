#!/usr/bin/env python3
"""Desktop interface for entropy assessment."""
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget, QAbstractItemView,
)
from core import run_batch

ROOT = pathlib.Path(__file__).resolve().parents[1]

class BatchWorker(QThread):
    progress = Signal(int, int, dict)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, paths, config, output):
        super().__init__()
        self.paths, self.config, self.output = paths, config, output

    def run(self):
        try:
            run_batch(self.paths, self.config, self.output,
                      lambda i, n, row: self.progress.emit(i, n, row))
            self.succeeded.emit(str(self.output))
        except Exception as error:
            self.failed.emit(str(error))

class Desktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('IP4 | Entropy & Health Assessment')
        self.resize(1440, 850)
        self.files, self.rows = [], []
        self.worker = None
        self._build()

    def _spin(self, value, minimum, maximum):
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    def _path_field(self, initial, directory=True):
        edit = QLineEdit(str(initial))
        choose = QPushButton('Browse')
        def browse():
            path = (QFileDialog.getExistingDirectory(self, 'Select directory', edit.text())
                    if directory else QFileDialog.getOpenFileName(self, 'Select executable', edit.text())[0])
            if path:
                edit.setText(path)
        choose.clicked.connect(browse)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        layout.addWidget(choose)
        return edit, row

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)
        vertical = QVBoxLayout(root)
        title = QLabel('Entropy & Health Assessment')
        title.setObjectName('title')
        vertical.addWidget(title)


        splitter = QSplitter(Qt.Horizontal)
        vertical.addWidget(splitter, 1)

        left = QGroupBox('1 · File Selection')
        ll = QVBoxLayout(left)
        buttons = QHBoxLayout()
        for text, action in [('Add files', self._add_files), ('Add folder', self._add_folder), ('Clear', self._clear)]:
            b = QPushButton(text)
            b.clicked.connect(action)
            buttons.addWidget(b)
        ll.addLayout(buttons)
        self.file_list = QListWidget()
        ll.addWidget(self.file_list, 1)
        self.file_count = QLabel('0 files (max 200)')
        ll.addWidget(self.file_count)
        splitter.addWidget(left)

        mid = QWidget()
        ml = QVBoxLayout(mid)
        ml.setContentsMargins(0, 0, 0, 0)
        settings = QGroupBox('2 · Test Selection')
        sl = QVBoxLayout(settings)
        data = QGroupBox('Data configuration')
        form = QFormLayout(data)
        self.bits = QComboBox()
        self.bits.addItems(['1', '4', '8'])
        self.encoding = QComboBox()
        self.encoding.addItems(['byte-per-symbol', 'packed-msb'])
        self.samples = self._spin(1_000_000, 1, 100_000_000)
        form.addRow('Bits per symbol', self.bits)
        form.addRow('Storage', self.encoding)
        form.addRow('Samples per file', self.samples)
        sl.addWidget(data)
        self.iid = QCheckBox('NIST IID')
        self.noniid = QCheckBox('NIST Non-IID')
        self.health = QCheckBox('RCT + APT')
        self.nist_verbosity = QComboBox()
        self.nist_verbosity.addItems([
            'Normal',
            'Detailed (-v)',
            'Full (-vv)'
        ])
        self.nist_verbosity.setCurrentIndex(2)
        for cb in (self.iid, self.noniid, self.health):
            cb.setChecked(True)
            sl.addWidget(cb)
        cutoff = QGroupBox('Health Test Parameters')
        cf = QFormLayout(cutoff)
        self.rct = self._spin(22, 2, 1_000_000)
        self.apt_window = self._spin(512, 2, 1_000_000)
        self.apt_cutoff = self._spin(320, 2, 1_000_000)
        cf.addRow('RCT cutoff', self.rct)
        cf.addRow('APT window', self.apt_window)
        cf.addRow('APT cutoff', self.apt_cutoff)
        sl.addWidget(cutoff)
        verbosity_form = QFormLayout()
        verbosity_form.addRow(
            'NIST output detail',
            self.nist_verbosity
        )
        sl.addLayout(verbosity_form)
        self.workers = self._spin(2, 1, 16)
        self.timeout = self._spin(1800, 1, 86400)
        ef = QFormLayout()
        ef.addRow('Parallel workers', self.workers)
        ef.addRow('Timeout (seconds)', self.timeout)
        sl.addLayout(ef)
        ml.addWidget(settings)
        ml.addStretch()
        splitter.addWidget(mid)

        right = QGroupBox('3 · Results')
        rl = QVBoxLayout(right)
        rl.addWidget(QLabel('Select a result row to inspect output and test details'))
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['File', 'Execution', 'IID', 'Non-IID', 'Health alarm', 'Time (s)'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 210)
        self.table.itemSelectionChanged.connect(self._detail)
        rl.addWidget(self.table, 2)
        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setPlaceholderText('Results appear after execution. Exit code 0 is not an IID pass decision.')
        rl.addWidget(self.detail, 2)
        splitter.addWidget(right)
        splitter.setSizes([310, 360, 720])

        paths = QGroupBox('Execution & Paths')
        pf = QFormLayout(paths)
        self.nist, w = self._path_field((ROOT / '.nist_location').read_text(encoding='utf-8').strip() if (ROOT / '.nist_location').exists() else ROOT.parent / 'SP800-90B_EntropyAssessment' / 'cpp')
        pf.addRow('NIST cpp directory', w)
        self.engine, w = self._path_field(ROOT / 'engine' / ('ip4_health.exe' if sys.platform == 'win32' else 'ip4_health'), False)
        pf.addRow('Health engine binary', w)
        self.output, w = self._path_field(ROOT / 'results')
        pf.addRow('Results directory', w)
        vertical.addWidget(paths)
        actions = QHBoxLayout()
        self.run_button = QPushButton('▶  Apply Selected Tests')
        self.run_button.clicked.connect(self._start)
        actions.addWidget(self.run_button)
        open_button = QPushButton('Open results folder')
        open_button.clicked.connect(self._open_output)
        actions.addWidget(open_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        actions.addWidget(self.progress, 1)
        self.info = QLabel('Ready')
        actions.addWidget(self.info)
        vertical.addLayout(actions)
        self.setStyleSheet('''
            QMainWindow { background: #f6f8fb; }
            QLabel#title { font-size: 22px; font-weight: 700; }
            QGroupBox { font-weight: 600; margin-top: 9px; padding-top: 10px; }
            QPushButton { padding: 7px 10px; }
            QLineEdit, QComboBox, QSpinBox { min-height: 26px; }
        ''')

    def _add_paths(self, paths):
        existing = set(self.files)
        for path in paths:
            resolved = str(pathlib.Path(path).resolve())
            if resolved.lower().endswith('.bin') and resolved not in existing:
                self.files.append(resolved)
                existing.add(resolved)
        if len(self.files) > 200:
            self.files = self.files[:200]
            QMessageBox.warning(self, 'Batch limit', 'Maximum 200 files per batch')
        self.file_list.clear()
        self.file_list.addItems([pathlib.Path(p).name for p in self.files])
        self.file_count.setText(f'{len(self.files)} files (max 200)')

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose data', '', 'Binary files (*.bin);;All files (*)')
        self._add_paths(files)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose data folder')
        if folder:
            self._add_paths(sorted(pathlib.Path(folder).glob('*.bin')))

    def _clear(self):
        if not (self.worker and self.worker.isRunning()):
            self.files.clear()
            self._add_paths([])

    def _start(self):
        if not self.files:
            return QMessageBox.warning(self, 'Missing data', 'Please add .bin files')
        if not (self.iid.isChecked() or self.noniid.isChecked() or self.health.isChecked()):
            return QMessageBox.warning(self, 'No tests', 'Choose at least one test')
        if self.apt_cutoff.value() > self.apt_window.value():
            return QMessageBox.warning(self, 'Invalid cutoff', 'APT cutoff cannot exceed its window')
        out = pathlib.Path(self.output.text()).expanduser().resolve()
        # Do not overwrite a prior experiment run.
        if (out / 'results.csv').exists():
            out = out.parent / (out.name + '_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            self.output.setText(str(out))
        cfg = dict(bits=int(self.bits.currentText()), encoding=self.encoding.currentText(),
                   samples=self.samples.value(), iid=self.iid.isChecked(),
                   non_iid=self.noniid.isChecked(), health=self.health.isChecked(),
                   rct_cutoff=self.rct.value(), apt_window=self.apt_window.value(),
                   apt_cutoff=self.apt_cutoff.value(), workers=self.workers.value(),
                   timeout=self.timeout.value(),
                   nist_verbosity=self.nist_verbosity.currentIndex(),
                   nist_dir=self.nist.text(),
                   health_bin=self.engine.text())
        self.rows = []
        self.table.setRowCount(0)
        self.detail.clear()
        self.progress.setValue(0)
        self.run_button.setEnabled(False)
        self.worker = BatchWorker(list(self.files), cfg, out)
        self.worker.progress.connect(self._progress)
        self.worker.succeeded.connect(self._complete)
        self.worker.failed.connect(self._error)
        self.worker.start()
        self.info.setText('Running...')

    def _progress(self, i, n, row):
        self.rows.append(row)
        index = self.table.rowCount()
        self.table.insertRow(index)
        values = [row['file'], row['status'], row['iid_status'], row['non_iid_status'],
                  str(row['health_alarm']) if row['health_status'] == 'ok' else row['health_status'],
                  str(row['seconds'])]
        for j, value in enumerate(values):
            self.table.setItem(index, j, QTableWidgetItem(value))
        self.progress.setValue(round(i * 100 / n))
        self.info.setText(f'{i}/{n} processed')

    def _detail(self):
        index = self.table.currentRow()
        if not (0 <= index < len(self.rows)):
            return
        row = self.rows[index]
        result = json.dumps(row, indent=2, ensure_ascii=False)
        for track in ('iid', 'non_iid'):
            raw = row.get('raw_' + track)
            if raw and pathlib.Path(raw).is_file():
                result += '\n\n========== ' + track.upper() + ' NIST RAW OUTPUT ==========\n'
                result += pathlib.Path(raw).read_text(errors='replace')[:100000]
        self.detail.setPlainText(result)

    def _complete(self, output):
        self.run_button.setEnabled(True)
        self.info.setText(f'Complete · {len(self.rows)} files')
        QMessageBox.information(self, 'Finished', f'Experiment output saved to:\n{output}')

    def _error(self, error):
        self.run_button.setEnabled(True)
        self.info.setText('Execution failed')
        QMessageBox.critical(self, 'Batch error', error)

    def _open_output(self):
        folder = pathlib.Path(self.output.text())
        if not folder.exists():
            return QMessageBox.information(self, 'No results', 'Results directory does not exist yet')
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))


def main():
    app = QApplication(sys.argv)
    window = Desktop()
    window.show()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
