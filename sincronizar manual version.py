import sys
import os
import json
import datetime
import logging
import pythoncom # Importar pythoncom para CoInitialize/CoUninitialize
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QDateEdit, QSpinBox,
    QMessageBox
)
from PyQt5.QtCore import (
    QThread, pyqtSignal, QObject, QDate, QTime, QDateTime
)
from PyQt5.QtGui import QFont

# --- Configuración del Logging ---
log_file_path = "sincronizador_log.txt"
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Creamos un logger específico para la GUI para evitar duplicar mensajes si se usan otros handlers.
gui_logger = logging.getLogger('gui_logger')
gui_logger.setLevel(logging.INFO)

# --- Nuevo: Objeto QObject para recibir señales de log en el hilo principal ---
class LogReceiver(QObject):
    log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

# --- Modificado: GuiLogHandler ya no hereda de QObject ---
class GuiLogHandler(logging.Handler):
    def __init__(self, receiver_instance):
        super().__init__()
        self.receiver = receiver_instance # Referencia al objeto LogReceiver

    def emit(self, record):
        log_entry = self.format(record)
        # Emitir la señal a través del LogReceiver
        self.receiver.log_signal.emit(log_entry)

# La instancia de gui_handler se moverá a MainWindow.__init__
# para que se inicialice con la instancia de LogReceiver.
# Por ahora, la declaramos aquí para que el nombre sea accesible globalmente.
gui_handler = None # Se inicializará en MainWindow

# --- Clase Trabajadora para la Sincronización (Ejecutada en un Hilo Separado) ---
class SyncWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, devices, selected_date, selected_time):
        super().__init__()
        self.devices = devices
        self.selected_date = selected_date
        self.selected_time = selected_time
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run_synchronization(self):
        try:
            # Inicializar el entorno COM para este hilo
            pythoncom.CoInitialize()
            import win32com.client
        except ImportError:
            self.error.emit("Error: 'pywin32' no está instalado o no es un entorno Windows compatible.")
            self.finished.emit()
            return
        except Exception as e:
            self.error.emit(f"Error al inicializar COM: {e}")
            self.finished.emit()
            return

        try:
            year = self.selected_date.year()
            month = self.selected_date.month()
            day = self.selected_date.day()
            hour = self.selected_time.hour()
            minute = self.selected_time.minute()
            second = self.selected_time.second()

            combined_datetime_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

            self.progress.emit(f"Script de sincronización de hora ZKTeco iniciado - {datetime.datetime.now()}")
            self.progress.emit(f"Se intentará sincronizar los dispositivos a la hora: {combined_datetime_str}")

            success_count = 0
            total_devices = len(self.devices)

            for i, disp in enumerate(self.devices):
                if not self._is_running:
                    self.progress.emit("Sincronización cancelada por el usuario.")
                    break

                ip = disp.get("ip")
                puerto = disp.get("puerto")
                numero_maquina = disp.get("numero_maquina")

                if not all([ip, puerto, numero_maquina is not None]):
                    self.progress.emit(f"Advertencia: Dispositivo con información incompleta en JSON: {disp}. Saltando.")
                    continue

                self.progress.emit(f"\nIntentando conectar con el dispositivo {ip}:{puerto} (Máquina #{numero_maquina})...")

                zk = None # Inicializar zk a None
                try:
                    zk = win32com.client.Dispatch("ZKEMKeeper.ZKEM.1")
                except Exception as e:
                    error_msg = f"Error al crear el objeto ZKEMKeeper para {ip}: {e}"
                    error_msg += "\nAsegúrate de que zkemkeeper.dll esté correctamente registrada (ejecutar registrar_sdk.bat como administrador) y que la arquitectura de Python sea 32-bit."
                    self.progress.emit(error_msg)
                    continue

                if zk.Connect_Net(ip, puerto):
                    self.progress.emit(f"Conexión exitosa con {ip}.")

                    if zk.SetDeviceTime2(numero_maquina, year, month, day, hour, minute, second):
                        self.progress.emit(f"Hora del dispositivo {ip} sincronizada con éxito a: {combined_datetime_str}.")
                        success_count += 1
                    else:
                        error_code = zk.GetLastError()
                        self.progress.emit(f"Error: No se pudo sincronizar la hora del dispositivo {ip}. Código de error: {error_code}")

                    zk.Disconnect()
                    self.progress.emit(f"Desconectado de {ip}.")
                    zk = None # Liberar el objeto COM
                else:
                    error_code = zk.GetLastError()
                    error_msg = f"Error al conectar con {ip}. Código de error: {error_code}"
                    error_msg += "\nPosibles causas: IP incorrecta, dispositivo apagado, puerto bloqueado (firewall), problema de red."
                    self.progress.emit(error_msg)
                    if zk:
                        zk = None # Liberar el objeto COM incluso si la conexión falla

            self.progress.emit(f"\nProceso de sincronización de hora ZKTeco finalizado. Dispositivos sincronizados: {success_count}/{total_devices}.")
        finally:
            # Desinicializar el entorno COM al finalizar el hilo
            pythoncom.CoUninitialize()
            self.finished.emit() # Asegura que esta sea la última cosa en finally

# --- Ventana Principal de la Aplicación ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sincronizador de Hora ZKTeco")
        self.setGeometry(100, 100, 1024, 768)

        self.devices = []
        self.load_devices()

        # Crear la instancia de LogReceiver antes de init_ui y setup_logging
        self.log_receiver = LogReceiver(self) # Pasa self como parent

        # Modificado: Inicializar gui_handler con la instancia de LogReceiver
        global gui_handler
        if gui_handler in gui_logger.handlers: # Asegurarse de que no se añada dos veces si ya existe
            gui_logger.removeHandler(gui_handler)
        gui_handler = GuiLogHandler(self.log_receiver)
        gui_logger.addHandler(gui_handler)

        self.init_ui()
        self.setup_logging()

        self.worker_thread = None
        self.sync_worker = None

    def load_devices(self):
        json_file_name = "dispositivos.json"
        if not os.path.exists(json_file_name):
            self.show_message_box(
                "Error de Archivo",
                f"El archivo '{json_file_name}' no se encontró en la misma carpeta que el ejecutable.\n"
                "Por favor, crea este archivo con la configuración de tus dispositivos ZKTeco."
            )
            return

        try:
            with open(json_file_name, "r", encoding="utf-8") as f:
                self.devices = json.load(f)
            gui_logger.info(f"Dispositivos cargados desde '{json_file_name}': {len(self.devices)} encontrados.")
        except json.JSONDecodeError as e:
            self.show_message_box(
                "Error de JSON",
                f"Error al leer el archivo '{json_file_name}'. Asegúrate de que sea un JSON válido.\nDetalle: {e}"
            )
        except Exception as e:
            self.show_message_box(
                "Error de Carga",
                f"Ocurrió un error inesperado al cargar '{json_file_name}': {e}"
            )

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.date_label = QLabel("Selecciona la fecha:")
        layout.addWidget(self.date_label)

        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setFont(QFont("Arial", 20))
        self.date_edit.setMinimumHeight(50)
        layout.addWidget(self.date_edit)

        time_selection_layout = QHBoxLayout()
        time_selection_layout.setSpacing(20)

        self.hour_label = QLabel("HH:")
        self.hour_label.setFont(QFont("Arial", 18))
        time_selection_layout.addWidget(self.hour_label)

        self.hour_spinbox = QSpinBox(self)
        self.hour_spinbox.setRange(0, 23)
        self.hour_spinbox.setValue(QTime.currentTime().hour())
        self.hour_spinbox.setFont(QFont("Arial", 24))
        self.hour_spinbox.setMinimumSize(80, 60)
        time_selection_layout.addWidget(self.hour_spinbox)

        self.minute_label = QLabel("MM:")
        self.minute_label.setFont(QFont("Arial", 18))
        time_selection_layout.addWidget(self.minute_label)

        self.minute_spinbox = QSpinBox(self)
        self.minute_spinbox.setRange(0, 59)
        self.minute_spinbox.setValue(QTime.currentTime().minute())
        self.minute_spinbox.setFont(QFont("Arial", 24))
        self.minute_spinbox.setMinimumSize(80, 60)
        time_selection_layout.addWidget(self.minute_spinbox)

        layout.addLayout(time_selection_layout)

        self.sync_button = QPushButton("Sincronizar Hora Seleccionada")
        self.sync_button.clicked.connect(self.start_synchronization)
        self.sync_button.setFont(QFont("Arial", 18))
        self.sync_button.setMinimumHeight(60)
        layout.addWidget(self.sync_button)

        self.sync_with_system_button = QPushButton("Sincronizar con la Hora del Equipo")
        self.sync_with_system_button.clicked.connect(self.sync_with_system_time)
        self.sync_with_system_button.setFont(QFont("Arial", 18))
        self.sync_with_system_button.setMinimumHeight(60)
        layout.addWidget(self.sync_with_system_button)

        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Arial", 12))
        layout.addWidget(self.log_display)

        info_label = QLabel(
            "Nota: La sincronización establecerá la hora de los dispositivos ZKTeco a la fecha y hora seleccionada arriba."
            "\nPara el correcto funcionamiento, asegúrate de que 'zkemkeeper.dll' esté registrada y Python sea de 32 bits."
        )
        info_label.setWordWrap(True)
        info_label.setFont(QFont("Arial", 10))
        layout.addWidget(info_label)

    def setup_logging(self):
        # Conectar la señal del LogReceiver al slot de actualización de la GUI
        self.log_receiver.log_signal.connect(self.update_log_display)

    def update_log_display(self, message):
        self.log_display.append(message)

    def start_synchronization(self):
        if not self.devices:
            self.show_message_box("Advertencia", "No hay dispositivos cargados para sincronizar.")
            return

        selected_date = self.date_edit.date()
        selected_time = QTime(self.hour_spinbox.value(), self.minute_spinbox.value(), 0)

        self.sync_button.setEnabled(False)
        self.sync_with_system_button.setEnabled(False)
        self.log_display.clear()
        gui_logger.info("Iniciando sincronización...")

        self.worker_thread = QThread()
        self.sync_worker = SyncWorker(self.devices, selected_date, selected_time)
        self.sync_worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.sync_worker.run_synchronization)
        # Conectar la señal finished del worker directamente a on_sync_finished
        self.sync_worker.finished.connect(self.on_sync_finished)
        self.sync_worker.finished.connect(self.worker_thread.quit)
        self.sync_worker.finished.connect(self.sync_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.sync_worker.progress.connect(self.update_log_display)
        self.sync_worker.error.connect(self.handle_worker_error)

        self.worker_thread.start()

    def sync_with_system_time(self):
        current_datetime = QDateTime.currentDateTime()
        self.date_edit.setDate(current_datetime.date())
        self.hour_spinbox.setValue(current_datetime.time().hour())
        self.minute_spinbox.setValue(current_datetime.time().minute())
        self.start_synchronization()

    def on_sync_finished(self):
        self.sync_button.setEnabled(True)
        self.sync_with_system_button.setEnabled(True)
        gui_logger.info("Proceso de sincronización finalizado.")

    def handle_worker_error(self, message):
        gui_logger.error(f"Error del Hilo de Sincronización: {message}")
        self.show_message_box("Error de Sincronización", message)
        self.on_sync_finished()

    def show_message_box(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

if __name__ == "__main__":
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except Exception as e:
            print(f"Advertencia: No se pudo crear el directorio para el archivo de log: {e}")

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    # Limpieza explícita de handlers antes de la salida para evitar RuntimeError
    def cleanup_logging():
        # Remover el handler personalizado del logger de la GUI
        global gui_handler # Necesario para modificar la variable global
        if gui_handler in gui_logger.handlers:
            gui_logger.removeHandler(gui_handler)
            # No llamar a .close() en GuiLogHandler ya que no es un QObject y no tiene ese método
            # El objeto LogReceiver se destruirá con su padre (MainWindow)
            gui_handler = None # Eliminar la referencia al handler

        # Remover otros handlers del logger raíz si los hay (ej. StreamHandler de basicConfig)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            if hasattr(handler, 'close'): # Solo si el handler tiene un método close
                handler.close()

    app.aboutToQuit.connect(cleanup_logging)

    exit_code = app.exec()
    sys.exit(exit_code)
