from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from constants import (
    DEFAULT_PANEL_HEIGHT,
    DEFAULT_PANEL_WIDTH,
    MAX_PANEL_COUNT,
    MAX_PANEL_HEIGHT,
    MAX_PANEL_WIDTH,
    MIN_PANEL_HEIGHT,
    MIN_PANEL_WIDTH,
)


class ProjectionSettingsDialog(QDialog):
    def __init__(self, panel_sizes, output_size=None, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configuracoes de projecao")
        self.output_width, self.output_height = output_size or (0, 0)
        self.size_inputs = []
        self.panel_container = QWidget(self)
        self.panel_layout = QVBoxLayout(self.panel_container)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(8)

        layout = QVBoxLayout(self)
        layout.addWidget(self.build_output_label())

        actions_layout = QHBoxLayout()
        self.add_button = QPushButton("+ Parte")
        self.remove_button = QPushButton("- Remover ultima")
        self.add_button.clicked.connect(self.add_panel)
        self.remove_button.clicked.connect(self.remove_last_panel)
        actions_layout.addWidget(self.add_button)
        actions_layout.addWidget(self.remove_button)
        actions_layout.addStretch(1)
        layout.addLayout(actions_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.panel_container)
        layout.addWidget(scroll_area, 1)

        self.validation_label = QLabel(self)
        self.validation_label.setWordWrap(True)
        self.validation_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.validation_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        for panel_size in panel_sizes:
            self.add_panel(panel_size=panel_size)

        if not self.size_inputs:
            self.add_panel()

        self.validate_sizes()

    def build_output_label(self):
        if self.output_width and self.output_height:
            text = (
                "Defina a largura e altura de cada parte em pixels. "
                f"Saida selecionada: {self.output_width}x{self.output_height} px."
            )
        else:
            text = (
                "Defina a largura e altura de cada parte em pixels. "
                "Nenhuma saida foi detectada para validacao."
            )
        return QLabel(text)

    def add_panel(self, _checked=False, panel_size=None):
        if len(self.size_inputs) >= MAX_PANEL_COUNT:
            return

        width, height = panel_size or (DEFAULT_PANEL_WIDTH, DEFAULT_PANEL_HEIGHT)
        index = len(self.size_inputs)
        group, width_input, height_input = self.build_panel_group(
            index,
            (width, height),
        )
        self.size_inputs.append((width_input, height_input, group))
        self.panel_layout.addWidget(group)
        self.renumber_groups()
        self.validate_sizes()

    def remove_last_panel(self):
        if len(self.size_inputs) <= 1:
            return

        _width_input, _height_input, group = self.size_inputs.pop()
        self.panel_layout.removeWidget(group)
        group.setParent(None)
        group.deleteLater()
        self.renumber_groups()
        self.validate_sizes()

    def renumber_groups(self):
        for index, (_width_input, _height_input, group) in enumerate(
            self.size_inputs
        ):
            group.setTitle(f"Parte {index + 1}")

        self.add_button.setEnabled(len(self.size_inputs) < MAX_PANEL_COUNT)
        self.remove_button.setEnabled(len(self.size_inputs) > 1)

    def build_panel_group(self, index, panel_size):
        width, height = panel_size
        width_input = self.build_dimension_input(
            width,
            MIN_PANEL_WIDTH,
            MAX_PANEL_WIDTH,
        )
        height_input = self.build_dimension_input(
            height,
            MIN_PANEL_HEIGHT,
            MAX_PANEL_HEIGHT,
        )
        width_input.valueChanged.connect(self.validate_sizes)
        height_input.valueChanged.connect(self.validate_sizes)

        form_layout = QFormLayout()
        form_layout.addRow("Largura (px)", width_input)
        form_layout.addRow("Altura (px)", height_input)

        dimensions_layout = QHBoxLayout()
        dimensions_layout.addLayout(form_layout)
        dimensions_layout.addStretch(1)

        group = QGroupBox(f"Parte {index + 1}")
        group.setLayout(dimensions_layout)
        return group, width_input, height_input

    @staticmethod
    def build_dimension_input(value, minimum, maximum):
        spin_box = QSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setSingleStep(10)
        spin_box.setValue(int(value))
        spin_box.setSuffix(" px")
        return spin_box

    def validate_sizes(self):
        total_width = sum(
            width_input.value()
            for width_input, _height_input, _group in self.size_inputs
        )
        max_height = max(
            [
                height_input.value()
                for _width_input, height_input, _group in self.size_inputs
            ]
            or [0]
        )

        messages = [
            f"Partes: {len(self.size_inputs)} | "
            f"largura usada: {total_width}px | "
            f"altura maxima usada: {max_height}px"
        ]
        is_valid = True

        if self.output_width and total_width > self.output_width:
            is_valid = False
            messages.append(
                f"Erro: a soma das larguras ({total_width}px) ultrapassa "
                f"a largura da saida ({self.output_width}px)."
            )

        if self.output_height and max_height > self.output_height:
            is_valid = False
            messages.append(
                f"Erro: uma ou mais alturas ultrapassam a altura da saida "
                f"({self.output_height}px)."
            )

        if is_valid:
            self.validation_label.setStyleSheet("color: #0b4d2a;")
            if self.output_width and self.output_height:
                free_width = self.output_width - total_width
                messages.append(f"OK: largura livre na saida: {free_width}px.")
            else:
                messages.append("OK: validacao local aplicada.")
        else:
            self.validation_label.setStyleSheet("color: #a00000; font-weight: 600;")

        self.validation_label.setText("\n".join(messages))
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(is_valid)

    def panel_sizes(self):
        return [
            (width_input.value(), height_input.value())
            for width_input, height_input, _group in self.size_inputs
        ]
