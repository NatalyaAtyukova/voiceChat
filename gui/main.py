import sys
import subprocess
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet
from registration_window import RegistrationWindow

# Запуск FastAPI в фоновом режиме
api_process = subprocess.Popen([sys.executable, "run_api.py"])

# Запуск PyQt-приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml')

    window = RegistrationWindow()
    window.show()

    # Закрытие FastAPI при выходе из приложения
    exit_code = app.exec_()
    api_process.terminate()
    sys.exit(exit_code)