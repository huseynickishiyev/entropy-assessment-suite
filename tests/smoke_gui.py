import pathlib
import sys
from PySide6.QtWidgets import QApplication
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'app'))
from gui import Desktop
app = QApplication([])
window = Desktop()
window.show()
app.processEvents()
assert window.isVisible()
assert window.table.columnCount() == 6
assert window.run_button.isEnabled()
window.close()
print('Qt GUI smoke test passed')
