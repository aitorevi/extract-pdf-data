"""
Editor unificado de plantillas con PyQt6 y estilos QSS.
Mantiene la funcionalidad de selección de coordenadas pero con una UI moderna.
"""

import sys
import json
import os
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QScrollArea,
    QFrame, QInputDialog
)
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QImage


# CAMPOS PREDEFINIDOS - Modifica esto según tus necesidades
CAMPOS_PREDEFINIDOS = [
    {"nombre": "num-factura", "tipo": "texto"},
    {"nombre": "fecha-factura", "tipo": "fecha"},
    {"nombre": "base", "tipo": "numerico"},
    {"nombre": "iva", "tipo": "numerico"},
    {"nombre": "total", "tipo": "numerico"},
]


class CanvasSeleccion(QLabel):
    """Widget para mostrar el PDF y seleccionar coordenadas"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.punto_inicio = None
        self.punto_fin = None
        self.rectangulo_actual = None
        self.campo_seleccionado = None
        self.callback_seleccion = None

    def mousePressEvent(self, event):
        """Al hacer clic"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.campo_seleccionado is None:
                # Notificar que no hay campo seleccionado
                if hasattr(self.parent(), 'actualizar_estado_seleccion'):
                    self.parent().actualizar_estado_seleccion('advertencia')
                return

            self.punto_inicio = event.pos()
            self.punto_fin = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        """Al arrastrar"""
        if self.punto_inicio and self.campo_seleccionado:
            self.punto_fin = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Al soltar el clic"""
        if event.button() == Qt.MouseButton.LeftButton and self.punto_inicio:
            if self.campo_seleccionado is None:
                return

            self.punto_fin = event.pos()

            # Verificar que no sea un clic sin arrastre
            if abs(self.punto_fin.x() - self.punto_inicio.x()) < 5 or \
               abs(self.punto_fin.y() - self.punto_inicio.y()) < 5:
                self.punto_inicio = None
                self.punto_fin = None
                self.update()
                return

            # Notificar selección
            if self.callback_seleccion:
                x1 = min(self.punto_inicio.x(), self.punto_fin.x())
                y1 = min(self.punto_inicio.y(), self.punto_fin.y())
                x2 = max(self.punto_inicio.x(), self.punto_fin.x())
                y2 = max(self.punto_inicio.y(), self.punto_fin.y())

                self.callback_seleccion(x1, y1, x2, y2)

            self.punto_inicio = None
            self.punto_fin = None
            self.update()

    def paintEvent(self, event):
        """Dibujar el canvas"""
        super().paintEvent(event)

        if self.punto_inicio and self.punto_fin:
            painter = QPainter(self)
            pen = QPen(QColor(255, 0, 0), 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)

            rect = QRect(self.punto_inicio, self.punto_fin)
            painter.drawRect(rect.normalized())


class EditorPlantillasQt(QMainWindow):
    def __init__(self, pdf_path, plantilla_existente=None):
        super().__init__()

        self.pdf_path = pdf_path
        self.imagen_pil = None
        self.imagen_original_pil = None
        self.campos = {}  # {nombre_campo: coordenadas} o None si no está capturado
        self.campo_seleccionado = None
        self.plantilla_cargada = plantilla_existente

        # Inicializar campos
        for campo_def in CAMPOS_PREDEFINIDOS:
            self.campos[campo_def['nombre']] = None

        # Si hay plantilla cargada, cargar coordenadas existentes
        if plantilla_existente and 'campos' in plantilla_existente:
            for campo in plantilla_existente['campos']:
                if campo['nombre'] in self.campos:
                    self.campos[campo['nombre']] = campo['coordenadas']

        # Obtener dimensiones del PDF
        with pdfplumber.open(pdf_path) as pdf:
            self.pdf_width = pdf.pages[0].width
            self.pdf_height = pdf.pages[0].height

        self.init_ui()
        self.cargar_estilos()
        self.cargar_imagen_pdf()

    def init_ui(self):
        """Inicializar la interfaz de usuario"""
        self.setWindowTitle("Editor de Plantillas - PyQt6")

        # Tamaño de ventana
        screen = QApplication.primaryScreen().geometry()
        window_width = min(1400, screen.width() - 100)
        window_height = min(900, screen.height() - 100)
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # PANEL IZQUIERDO: Canvas PDF
        self.crear_panel_canvas(main_layout)

        # PANEL DERECHO: Controles
        self.crear_panel_controles(main_layout)

    def crear_panel_canvas(self, parent_layout):
        """Crear el área del canvas PDF"""
        scroll_area = QScrollArea()
        scroll_area.setObjectName("canvasPDF")
        scroll_area.setWidgetResizable(True)

        # Canvas de selección
        self.canvas = CanvasSeleccion()
        self.canvas.setObjectName("imagenPDF")
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.callback_seleccion = self.al_seleccionar_coordenadas

        scroll_area.setWidget(self.canvas)
        parent_layout.addWidget(scroll_area, stretch=3)

    def crear_panel_controles(self, parent_layout):
        """Crear el panel lateral de controles"""
        panel = QWidget()
        panel.setObjectName("panelLateral")
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(300)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Título
        titulo = QLabel("EDITOR DE PLANTILLAS")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Label campo seleccionado
        self.label_seleccionado = QLabel("Ningún campo seleccionado")
        self.label_seleccionado.setObjectName("campoSeleccionado")
        self.label_seleccionado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_seleccionado.setWordWrap(True)
        self.label_seleccionado.setMinimumHeight(80)
        layout.addWidget(self.label_seleccionado)

        # Botón Guardar
        btn_guardar = QPushButton("✓ GUARDAR")
        btn_guardar.setObjectName("btnGuardar")
        btn_guardar.clicked.connect(self.guardar_plantilla)
        layout.addWidget(btn_guardar)

        # Botón Cargar Plantilla
        btn_cargar = QPushButton("📂 CARGAR\nOTRA PLANTILLA")
        btn_cargar.setObjectName("btnCargar")
        btn_cargar.clicked.connect(self.cargar_plantilla)
        layout.addWidget(btn_cargar)

        # Botón Cambiar PDF
        btn_pdf = QPushButton("🔄 CAMBIAR PDF")
        btn_pdf.setObjectName("btnCambiarPDF")
        btn_pdf.clicked.connect(self.cambiar_pdf)
        layout.addWidget(btn_pdf)

        # Botón Salir
        btn_salir = QPushButton("✕ SALIR")
        btn_salir.setObjectName("btnSalir")
        btn_salir.clicked.connect(self.close)
        layout.addWidget(btn_salir)

        # Separador
        sep = QLabel()
        sep.setObjectName("separador")
        layout.addWidget(sep)

        # Título Campos
        titulo_campos = QLabel("CAMPOS:")
        titulo_campos.setObjectName("tituloCampos")
        titulo_campos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo_campos)

        # Área de scroll para campos
        scroll_campos = QScrollArea()
        scroll_campos.setWidgetResizable(True)
        scroll_campos.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.widget_campos = QWidget()
        self.layout_campos = QVBoxLayout(self.widget_campos)
        self.layout_campos.setSpacing(5)

        scroll_campos.setWidget(self.widget_campos)
        layout.addWidget(scroll_campos, stretch=1)

        parent_layout.addWidget(panel, stretch=1)

        # Actualizar lista de campos
        self.actualizar_lista_campos()

    def actualizar_lista_campos(self):
        """Actualiza la lista de campos con botones"""
        # Limpiar layout
        while self.layout_campos.count():
            child = self.layout_campos.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, campo_def in enumerate(CAMPOS_PREDEFINIDOS):
            nombre = campo_def['nombre']
            tipo = campo_def['tipo']
            tiene_coords = self.campos[nombre] is not None

            # Frame para cada campo
            frame = QFrame()
            frame.setObjectName("frameCampo")
            frame_layout = QHBoxLayout(frame)
            frame_layout.setContentsMargins(5, 5, 5, 5)

            # Label del campo
            if tiene_coords:
                label = QLabel(f"{i+1}. {nombre}\n({tipo})")
                label.setObjectName("labelCampo")
                btn_texto = "✓ EDITAR"
                btn_obj_name = "btnEditar"
            else:
                label = QLabel(f"{i+1}. {nombre}\n({tipo})")
                label.setObjectName("labelCampoSin")
                btn_texto = "+ CAPTURAR"
                btn_obj_name = "btnCapturar"

            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            frame_layout.addWidget(label, stretch=1)

            # Botón capturar/editar
            btn = QPushButton(btn_texto)
            btn.setObjectName(btn_obj_name)
            btn.clicked.connect(lambda checked, n=nombre: self.seleccionar_campo_para_captura(n))
            frame_layout.addWidget(btn)

            self.layout_campos.addWidget(frame)

        # Espaciador al final
        self.layout_campos.addStretch()

    def seleccionar_campo_para_captura(self, nombre_campo):
        """Selecciona un campo para capturar sus coordenadas"""
        self.campo_seleccionado = nombre_campo
        self.canvas.campo_seleccionado = nombre_campo

        self.label_seleccionado.setText(f"SELECCIONADO:\n{nombre_campo}\n\nAhora arrastra sobre\nel PDF")
        self.label_seleccionado.setProperty("estado", "seleccionado")
        self.label_seleccionado.style().unpolish(self.label_seleccionado)
        self.label_seleccionado.style().polish(self.label_seleccionado)

        print(f"→ Campo seleccionado: {nombre_campo}")

    def actualizar_estado_seleccion(self, estado):
        """Actualiza el estado visual del label de selección"""
        if estado == 'advertencia':
            self.label_seleccionado.setText("⚠️ SELECCIONA\nUN CAMPO\nde la lista →")
            self.label_seleccionado.setProperty("estado", "advertencia")

        self.label_seleccionado.style().unpolish(self.label_seleccionado)
        self.label_seleccionado.style().polish(self.label_seleccionado)

    def al_seleccionar_coordenadas(self, x1, y1, x2, y2):
        """Callback cuando se seleccionan coordenadas en el canvas"""
        if not self.campo_seleccionado:
            return

        # Convertir a coordenadas PDF
        pdf_x0 = x1 / self.escala_x
        pdf_top = y1 / self.escala_y
        pdf_x1 = x2 / self.escala_x
        pdf_bottom = y2 / self.escala_y

        # Guardar coordenadas
        self.campos[self.campo_seleccionado] = [pdf_x0, pdf_top, pdf_x1, pdf_bottom]

        print(f"✓ Campo actualizado: {self.campo_seleccionado} -> {self.campos[self.campo_seleccionado]}")

        # Redibujar
        self.redibujar_campos()
        self.actualizar_lista_campos()

        # Actualizar label
        self.label_seleccionado.setText(f"✓ Capturado:\n{self.campo_seleccionado}\n\nSelecciona otro\no guarda")
        self.label_seleccionado.setProperty("estado", "capturado")
        self.label_seleccionado.style().unpolish(self.label_seleccionado)
        self.label_seleccionado.style().polish(self.label_seleccionado)

        # Limpiar selección
        self.campo_seleccionado = None
        self.canvas.campo_seleccionado = None

    def cargar_imagen_pdf(self):
        """Convierte el PDF a imagen"""
        print("Convirtiendo PDF a imagen...")
        imagenes = convert_from_path(self.pdf_path, dpi=150)
        self.imagen_original_pil = imagenes[0]
        self.imagen_pil = self.imagen_original_pil.copy()

        # Calcular escala
        self.escala_x = self.imagen_pil.width / self.pdf_width
        self.escala_y = self.imagen_pil.height / self.pdf_height

        # Redimensionar si es muy grande
        max_width = 1200
        max_height = 900
        if self.imagen_pil.width > max_width or self.imagen_pil.height > max_height:
            ratio = min(max_width / self.imagen_pil.width, max_height / self.imagen_pil.height)
            new_width = int(self.imagen_pil.width * ratio)
            new_height = int(self.imagen_pil.height * ratio)
            self.imagen_pil = self.imagen_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.imagen_original_pil = self.imagen_original_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.escala_x *= ratio
            self.escala_y *= ratio

        self.redibujar_campos()

    def redibujar_campos(self):
        """Redibuja todos los campos capturados"""
        self.imagen_pil = self.imagen_original_pil.copy()
        draw = ImageDraw.Draw(self.imagen_pil)

        for i, campo_def in enumerate(CAMPOS_PREDEFINIDOS, 1):
            nombre = campo_def['nombre']
            coords = self.campos[nombre]

            if coords:
                # Convertir coordenadas PDF a imagen
                ix0 = int(coords[0] * self.escala_x)
                iy0 = int(coords[1] * self.escala_y)
                ix1 = int(coords[2] * self.escala_x)
                iy1 = int(coords[3] * self.escala_y)

                # Dibujar rectángulo
                draw.rectangle([ix0, iy0, ix1, iy1], outline="green", width=3)

                # Dibujar etiqueta
                draw.text((ix0 + 5, iy0 + 5), f"{i}. {nombre}", fill="green")

        self.mostrar_imagen()

    def mostrar_imagen(self):
        """Muestra la imagen en el canvas"""
        # Convertir PIL a QPixmap
        img_rgb = self.imagen_pil.convert('RGB')
        data = img_rgb.tobytes('raw', 'RGB')
        qimage = QImage(data, img_rgb.width, img_rgb.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        self.canvas.setPixmap(pixmap)
        self.canvas.adjustSize()

    def cargar_plantilla(self):
        """Carga una plantilla existente"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar plantilla",
            "plantillas",
            "JSON files (*.json);;All files (*.*)"
        )

        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                plantilla = json.load(f)

            if 'campos' not in plantilla:
                QMessageBox.critical(self, "Error", "Plantilla inválida")
                return

            # Cargar coordenadas
            for campo in plantilla['campos']:
                if campo['nombre'] in self.campos:
                    self.campos[campo['nombre']] = campo['coordenadas']

            self.plantilla_cargada = plantilla
            self.redibujar_campos()
            self.actualizar_lista_campos()

            QMessageBox.information(self, "Cargado", f"Plantilla cargada:\n{os.path.basename(archivo)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar:\n{e}")

    def cambiar_pdf(self):
        """Cambia el PDF de referencia"""
        pdf_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            "facturas",
            "PDF files (*.pdf);;All files (*.*)"
        )

        if pdf_path:
            self.pdf_path = pdf_path
            self.cargar_imagen_pdf()

    def guardar_plantilla(self):
        """Guarda la plantilla"""
        print("\n=== GUARDANDO PLANTILLA ===")

        # Verificar que todos los campos estén capturados
        faltantes = [nombre for nombre, coords in self.campos.items() if coords is None]

        if faltantes:
            print(f"Faltan campos: {faltantes}")
            reply = QMessageBox.question(
                self,
                "Campos incompletos",
                f"Faltan campos:\n" + "\n".join(f"- {c}" for c in faltantes) + "\n\n¿Guardar de todos modos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                print("Guardado cancelado por usuario")
                return

        # Pedir información si es nueva
        if self.plantilla_cargada:
            proveedor_id = self.plantilla_cargada.get('proveedor_id', '')
            nombre_proveedor = self.plantilla_cargada.get('nombre_proveedor', '')
            print(f"Editando plantilla existente: {proveedor_id}")

            nombre_archivo, ok = QInputDialog.getText(
                self,
                "Guardar",
                "Nombre del archivo (sin .json):",
                text=proveedor_id
            )
            if not ok:
                return
        else:
            print("Creando plantilla nueva")
            nombre_archivo, ok = QInputDialog.getText(
                self,
                "Nombre de Plantilla",
                "Nombre del archivo (sin .json):"
            )
            if not ok or not nombre_archivo:
                print("Guardado cancelado - sin nombre")
                return

            proveedor_id, ok = QInputDialog.getText(
                self,
                "ID Proveedor",
                "ID del proveedor:"
            )
            if not ok:
                return

            nombre_proveedor, ok = QInputDialog.getText(
                self,
                "Nombre Proveedor",
                "Nombre del proveedor:"
            )
            if not ok:
                return

        if not nombre_archivo:
            print("Guardado cancelado - sin nombre de archivo")
            return

        print(f"Nombre archivo: {nombre_archivo}")
        print(f"Proveedor ID: {proveedor_id}")
        print(f"Nombre proveedor: {nombre_proveedor}")

        # Crear plantilla
        campos_lista = []
        for campo_def in CAMPOS_PREDEFINIDOS:
            nombre = campo_def['nombre']
            coords = self.campos[nombre]
            if coords:  # Solo incluir campos con coordenadas
                campos_lista.append({
                    "nombre": nombre,
                    "coordenadas": coords,
                    "tipo": campo_def['tipo']
                })

        print(f"Campos a guardar: {len(campos_lista)}")

        plantilla = {
            "proveedor_id": proveedor_id or "PROV_001",
            "nombre_proveedor": nombre_proveedor or "Proveedor",
            "pdf_referencia": self.pdf_path,
            "campos": campos_lista
        }

        # Guardar
        try:
            os.makedirs("plantillas", exist_ok=True)
            ruta = f"plantillas/{nombre_archivo}.json"

            print(f"Guardando en: {ruta}")

            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(plantilla, f, ensure_ascii=False, indent=4)

            print(f"✓ Archivo guardado exitosamente")
            QMessageBox.information(
                self,
                "Guardado",
                f"✓ Plantilla guardada:\n{ruta}\n\nCampos: {len(campos_lista)}"
            )
            print(f"✓ Plantilla guardada: {ruta}")

        except Exception as e:
            print(f"ERROR al guardar: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo guardar:\n{e}")

    def cargar_estilos(self):
        """Carga los estilos QSS desde el archivo"""
        try:
            with open('styles.qss', 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            print("✓ Estilos QSS cargados")
        except Exception as e:
            print(f"Error cargando estilos: {e}")


def main():
    app = QApplication(sys.argv)

    print("="*60)
    print("  EDITOR UNIFICADO DE PLANTILLAS - PyQt6")
    print("="*60)
    print("\nCampos predefinidos:")
    for i, campo in enumerate(CAMPOS_PREDEFINIDOS, 1):
        print(f"  {i}. {campo['nombre']} ({campo['tipo']})")

    plantilla_existente = None

    # Preguntar si quiere editar plantilla existente
    reply = QMessageBox.question(
        None,
        "Modo de edición",
        "¿Deseas editar una plantilla existente?\n\n(No = Crear nueva plantilla)",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        archivo, _ = QFileDialog.getOpenFileName(
            None,
            "Seleccionar plantilla a editar",
            "plantillas",
            "JSON files (*.json);;All files (*.*)"
        )

        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    plantilla_existente = json.load(f)
                print(f"✓ Plantilla cargada: {os.path.basename(archivo)}")
            except Exception as e:
                print(f"Error: {e}")
                QMessageBox.critical(None, "Error", f"No se pudo cargar la plantilla:\n{e}")
                return

    # Seleccionar PDF
    pdf_path, _ = QFileDialog.getOpenFileName(
        None,
        "Seleccionar PDF de factura",
        "facturas",
        "PDF files (*.pdf);;All files (*.*)"
    )

    if not pdf_path:
        print("No se seleccionó PDF")
        return

    print(f"✓ PDF seleccionado: {os.path.basename(pdf_path)}")

    try:
        ventana = EditorPlantillasQt(pdf_path, plantilla_existente)
        ventana.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
