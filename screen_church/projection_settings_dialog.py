from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from screen_church.constants import (
    MAX_PANEL_HEIGHT,
    MAX_PANEL_WIDTH,
    MIN_PANEL_HEIGHT,
    MIN_PANEL_WIDTH,
)


class ProjectionSettingsDialog(QDialog):
    def __init__(self, panel_sizes, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Configuracoes de projecao")
        self.size_inputs = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Defina a largura e altura de cada painel em pixels."))

        for index, panel_size in enumerate(panel_sizes):
            layout.addWidget(self.build_panel_group(index, panel_size))

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
        self.size_inputs.append((width_input, height_input))

        form_layout = QFormLayout()
        form_layout.addRow("Largura (px)", width_input)
        form_layout.addRow("Altura (px)", height_input)

        dimensions_layout = QHBoxLayout()
        dimensions_layout.addLayout(form_layout)

        group = QGroupBox(f"Painel {index + 1}")
        group.setLayout(dimensions_layout)
        return group

    @staticmethod
    def build_dimension_input(value, minimum, maximum):
        spin_box = QSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setSingleStep(10)
        spin_box.setValue(int(value))
        spin_box.setSuffix(" px")
        return spin_box

    def panel_sizes(self):
        return [
            (width_input.value(), height_input.value())
            for width_input, height_input in self.size_inputs
        ]
