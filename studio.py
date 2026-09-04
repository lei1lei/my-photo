# -*- coding: utf-8 -*-
"""
极速证件照工坊 V2.0 - 修复空白问题
完全离线，支持AI抠图、换背景、换服装、尺寸联动
"""
import sys
import os
import traceback
from PIL import Image
import numpy as np

# PyQt6 导入
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# AI抠图（如果失败则降级）
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except Exception:
    REMBG_AVAILABLE = False
    print("警告: rembg 导入失败，AI抠图不可用")

# ---------- 资源路径 ----------
def resource_path(relative_path):
    """获取资源的绝对路径（兼容开发和打包后）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------- 50种规格库 ----------
SPECS_DB = {
    "考试类": {
        "国考/省考": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "考研": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "英语四六级": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "教师资格证": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "法考": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "执业医师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "会计师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "一级建造师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "导游资格": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "计算机等级": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "普通话测试": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "专升本": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "高考报名": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "成人高考": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "MBA考试": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "执业药师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "护士执业": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "建造师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "初级会计": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "中级会计": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "注册会计师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "税务师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "资产评估师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "证券从业": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "基金从业": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "期货从业": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "银行从业": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "导游资格证": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "翻译资格": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "社会工作师": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
    },
    "证件类": {
        "一寸": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "二寸": {"mm": (35, 49), "dpi": 300, "bg": "#FFFFFF"},
        "小一寸": {"mm": (22, 32), "dpi": 300, "bg": "#FFFFFF"},
        "小二寸": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
        "身份证": {"mm": (26, 32), "dpi": 350, "bg": "#FFFFFF"},
        "驾驶证": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "居住证": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
        "社保卡": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
    },
    "签证类": {
        "中国护照": {"mm": (33, 48), "dpi": 300, "bg": "#FFFFFF"},
        "美国签证": {"mm": (51, 51), "dpi": 300, "bg": "#FFFFFF"},
        "日本签证": {"mm": (45, 45), "dpi": 300, "bg": "#FFFFFF"},
        "申根签证": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
        "英国签证": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
        "澳大利亚签证": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
        "新西兰签证": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
        "泰国签证": {"mm": (38, 50), "dpi": 300, "bg": "#FFFFFF"},
        "新加坡签证": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
        "韩国签证": {"mm": (35, 45), "dpi": 300, "bg": "#FFFFFF"},
    },
    "求职类": {
        "简历照": {"mm": (25, 35), "dpi": 300, "bg": "#003399"},
        "入职照": {"mm": (25, 35), "dpi": 300, "bg": "#FFFFFF"},
    }
}

# ---------- 主窗口 ----------
class IDPhotoStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("极速证件照工坊 V2.0")
        self.setGeometry(100, 100, 1400, 800)
        self.setAcceptDrops(True)
        
        # 数据
        self.original_pixmap = None
        self.processed_pixmap = None
        self.final_pixmap = None
        self.bg_color = QColor(255, 255, 255)
        self.clothes_name = "无"
        self.clothes_image = None
        self.clothes_hue = 0
        self.clothes_scale = 1.0
        self.clothes_dict = {}
        
        self.init_ui()
        self.load_clothes_from_folder()
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # ---- 左侧预览 ----
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        self.label_original = QLabel("📷 拖入图片或点击下方导入")
        self.label_original.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_original.setStyleSheet("border: 2px dashed #aaa; background:#f0f0f0; font-size:16px;")
        self.label_original.setMinimumSize(400, 500)
        
        self.label_result = QLabel("✨ 效果预览区")
        self.label_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_result.setStyleSheet("border: 2px solid #4CAF50; background:#fafafa; font-size:16px;")
        self.label_result.setMinimumSize(400, 500)
        
        preview_layout.addWidget(QLabel("【原始照片】"))
        preview_layout.addWidget(self.label_original)
        preview_layout.addWidget(QLabel("【最终效果】（按住鼠标对比原图）"))
        preview_layout.addWidget(self.label_result)
        
        # ---- 右侧操作面板 ----
        panel = QWidget()
        panel.setFixedWidth(450)
        panel_layout = QVBoxLayout(panel)
        scroll = QScrollArea()
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        
        # 1. 导入
        btn_import = QPushButton("📁 1. 导入照片")
        btn_import.setStyleSheet("font-size:14px; padding:8px;")
        btn_import.clicked.connect(self.import_image)
        panel_layout.addWidget(btn_import)
        
        # 2. 抠图
        self.btn_remove = QPushButton("✂️ 2. 一键AI抠图")
        self.btn_remove.setStyleSheet("font-size:14px; padding:8px; background:#4CAF50; color:white;")
        self.btn_remove.clicked.connect(self.do_remove_bg)
        if not REMBG_AVAILABLE:
            self.btn_remove.setEnabled(False)
            self.btn_remove.setText("✂️ AI抠图不可用（请联网重新下载）")
        panel_layout.addWidget(self.btn_remove)
        
        # 3. 背景
        gb_bg = QGroupBox("🎨 背景设置")
        gb_bg_layout = QVBoxLayout()
        color_row = QHBoxLayout()
        for hex_val, name in [("#FF0000","红底"), ("#003399","深蓝"), ("#FFFFFF","白底"), ("#1E90FF","亮蓝")]:
            btn = QPushButton(name)
            btn.setStyleSheet(f"background-color:{hex_val}; border:1px solid #333; min-height:30px; color:{'black' if hex_val=='#FFFFFF' else 'white'};")
            btn.clicked.connect(lambda checked, c=QColor(hex_val): self.set_bg_color(c))
            color_row.addWidget(btn)
        gb_bg_layout.addLayout(color_row)
        self.bg_preview = QLabel("当前: 白色")
        self.bg_preview.setStyleSheet("background-color:#FFFFFF; border:1px solid #000; min-height:25px;")
        gb_bg_layout.addWidget(self.bg_preview)
        gb_bg.setLayout(gb_bg_layout)
        panel_layout.addWidget(gb_bg)
        
        # 4. 服装
        gb_cloth = QGroupBox("👔 3. 选择服装")
        gb_cloth_layout = QVBoxLayout()
        self.cloth_grid = QGridLayout()
        self.cloth_btns = []
        self.cloth_row, self.cloth_col = 0, 0
        gb_cloth_layout.addLayout(self.cloth_grid)
        
        # 微调
        tune_row = QHBoxLayout()
        tune_row.addWidget(QLabel("色相:"))
        self.hue_slider = QSlider(Qt.Orientation.Horizontal)
        self.hue_slider.setRange(-180, 180)
        self.hue_slider.setValue(0)
        self.hue_slider.valueChanged.connect(self.adjust_clothes)
        tune_row.addWidget(self.hue_slider)
        gb_cloth_layout.addLayout(tune_row)
        
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("大小:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(50, 150)
        self.size_slider.setValue(100)
        self.size_slider.valueChanged.connect(self.adjust_clothes)
        size_row.addWidget(self.size_slider)
        gb_cloth_layout.addLayout(size_row)
        gb_cloth.setLayout(gb_cloth_layout)
        panel_layout.addWidget(gb_cloth)
        
        # 5. 尺寸
        gb_size = QGroupBox("📐 4. 尺寸/DPI联动")
        gb_size_layout = QFormLayout()
        
        self.px_w = QLineEdit("295")
        self.px_h = QLineEdit("413")
        self.px_w.textChanged.connect(self.on_size_changed)
        self.px_h.textChanged.connect(self.on_size_changed)
        gb_size_layout.addRow("像素(宽×高):", self.px_w)
        gb_size_layout.addRow("", self.px_h)
        
        self.mm_w = QLineEdit("25")
        self.mm_h = QLineEdit("35")
        self.mm_w.textChanged.connect(self.on_size_changed)
        self.mm_h.textChanged.connect(self.on_size_changed)
        gb_size_layout.addRow("打印尺寸(mm):", self.mm_w)
        gb_size_layout.addRow("", self.mm_h)
        
        self.dpi_edit = QLineEdit("300")
        self.dpi_edit.textChanged.connect(self.on_size_changed)
        gb_size_layout.addRow("DPI:", self.dpi_edit)
        
        self.lock_btn = QPushButton("🔒 锁定比例")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setChecked(True)
        self.lock_btn.clicked.connect(lambda: self.lock_btn.setText("🔓 已解锁" if not self.lock_btn.isChecked() else "🔒 锁定比例"))
        gb_size_layout.addRow(self.lock_btn)
        
        self.spec_combo = QComboBox()
        self.spec_combo.addItem("-- 选择预设规格 --")
        for cat, items in SPECS_DB.items():
            for name in items.keys():
                self.spec_combo.addItem(f"{cat} - {name}")
        self.spec_combo.currentIndexChanged.connect(self.load_preset)
        gb_size_layout.addRow("预设规格:", self.spec_combo)
        
        gb_size.setLayout(gb_size_layout)
        panel_layout.addWidget(gb_size)
        
        # 6. 导出
        gb_out = QGroupBox("💾 5. 导出")
        gb_out_layout = QFormLayout()
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(60, 100)
        self.quality_slider.setValue(90)
        gb_out_layout.addRow("图片质量:", self.quality_slider)
        self.name_edit = QLineEdit("我的证件照")
        gb_out_layout.addRow("文件名:", self.name_edit)
        btn_export = QPushButton("💾 导出最终图片")
        btn_export.setStyleSheet("font-size:14px; padding:8px; background:#2196F3; color:white;")
        btn_export.clicked.connect(self.export_image)
        gb_out_layout.addRow(btn_export)
        gb_out.setLayout(gb_out_layout)
        panel_layout.addWidget(gb_out)
        
        # 组装
        main_layout = QHBoxLayout()
        main_layout.addWidget(preview_widget, 3)
        main_layout.addWidget(scroll, 2)
        central.setLayout(main_layout)
        
        # 对比功能
        self.label_result.mousePressEvent = self.show_original
        self.label_result.mouseReleaseEvent = self.show_final
        
        # 添加"无"服装按钮
        btn_none = QPushButton("无")
        btn_none.setCheckable(True)
        btn_none.setChecked(True)
        btn_none.clicked.connect(lambda checked, n="无": self.set_clothes(n))
        self.cloth_grid.addWidget(btn_none, 0, 0)
        self.cloth_btns.append(btn_none)
        self.cloth_col = 1
        
    def load_clothes_from_folder(self):
        """加载服装图片"""
        clothes_dir = resource_path("clothes")
        if not os.path.exists(clothes_dir):
            os.makedirs(clothes_dir, exist_ok=True)
            # 创建说明文件
            with open(os.path.join(clothes_dir, "说明.txt"), "w", encoding="utf-8") as f:
                f.write("将透明背景的PNG服装图片放入此文件夹，程序会自动加载。\n文件名将显示为服装名称。")
            self.create_demo_clothes()
            return
        
        png_files = [f for f in os.listdir(clothes_dir) if f.lower().endswith('.png')]
        if not png_files:
            self.create_demo_clothes()
            return
        
        row, col = 0, self.cloth_col
        max_cols = 3
        for filename in png_files:
            name = os.path.splitext(filename)[0]
            try:
                img = Image.open(os.path.join(clothes_dir, filename)).convert('RGBA')
                self.clothes_dict[name] = img
                btn = QPushButton(name)
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked, n=name: self.set_clothes(n))
                self.cloth_grid.addWidget(btn, row, col)
                self.cloth_btns.append(btn)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"加载服装 {filename} 失败: {e}")
        
        if not self.clothes_dict:
            self.create_demo_clothes()
    
    def create_demo_clothes(self):
        """生成演示服装（彩色方块）"""
        demos = [
            ("男白衬衫", (200,200,200)),
            ("男蓝衬衫", (100,150,255)),
            ("男深西装", (50,50,100)),
            ("女白衬衫", (220,220,240)),
            ("女西装", (80,80,120)),
            ("圆领T恤", (100,200,100))
        ]
        row, col = 0, self.cloth_col
        max_cols = 3
        for name, color in demos:
            img = Image.new('RGBA', (200, 280), (*color, 200))
            self.clothes_dict[name] = img
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self.set_clothes(n))
            self.cloth_grid.addWidget(btn, row, col)
            self.cloth_btns.append(btn)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def set_bg_color(self, color):
        self.bg_color = color
        self.bg_preview.setStyleSheet(f"background-color:{color.name()}; border:1px solid #000; min-height:25px;")
        self.bg_preview.setText(color.name())
        self.update_final()
    
    def set_clothes(self, name):
        self.clothes_name = name
        for btn in self.cloth_btns:
            btn.setChecked(btn.text() == name)
        if name != "无" and name in self.clothes_dict:
            self.clothes_image = self.clothes_dict[name].copy()
        else:
            self.clothes_image = None
        self.update_final()
    
    def adjust_clothes(self):
        self.clothes_hue = self.hue_slider.value()
        self.clothes_scale = self.size_slider.value() / 100.0
        self.update_final()
    
    def import_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择照片", "", "图片 (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.load_image(path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.load_image(urls[0].toLocalFile())
    
    def load_image(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法加载图片")
            return
        self.original_pixmap = pixmap
        self.processed_pixmap = None
        self.final_pixmap = None
        self.label_original.setPixmap(pixmap.scaled(
            self.label_original.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.label_result.setPixmap(pixmap.scaled(
            self.label_result.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
    
    def do_remove_bg(self):
        if not REMBG_AVAILABLE:
            QMessageBox.critical(self, "错误", "AI抠图模块不可用，请检查网络后重新下载。")
            return
        if self.original_pixmap is None:
            QMessageBox.warning(self, "提示", "请先导入照片")
            return
        self.label_result.setText("⏳ AI处理中... 请稍候（约5-10秒）")
        QApplication.processEvents()
        try:
            qimg = self.original_pixmap.toImage()
            buf = qimg.bits()
            arr = np.frombuffer(buf, dtype=np.uint8).reshape(qimg.height(), qimg.width(), 4)
            pil_img = Image.fromarray(arr, 'RGBA')
            output = remove(pil_img).convert('RGBA')
            data = output.tobytes("raw", "RGBA")
            qimg_out = QImage(data, output.width, output.height, QImage.Format.Format_RGBA8888)
            self.processed_pixmap = QPixmap.fromImage(qimg_out)
            self.update_final()
            QMessageBox.information(self, "完成", "✅ 抠图成功！现在可以换背景和服装了。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"❌ 抠图失败\n{str(e)}\n\n首次使用需联网下载模型(约95MB)，请保持网络连接。")
    
    def update_final(self):
        if self.processed_pixmap is None:
            return
        pil_person = self.pil_from_qpixmap(self.processed_pixmap)
        if pil_person is None:
            return
        w, h = pil_person.size
        # 背景
        bg = Image.new('RGBA', (w, h), (self.bg_color.red(), self.bg_color.green(), self.bg_color.blue(), 255))
        final = bg.copy()
        final.paste(pil_person, (0, 0), pil_person)
        # 服装
        if self.clothes_image and self.clothes_name != "无":
            cloth = self.clothes_image.copy()
            if self.clothes_hue != 0:
                cloth = cloth.convert('HSV')
                np_img = np.array(cloth)
                np_img[:,:,0] = (np_img[:,:,0] + self.clothes_hue) % 180
                cloth = Image.fromarray(np_img, 'HSV').convert('RGBA')
            scale = self.clothes_scale
            new_size = (int(cloth.width * scale), int(cloth.height * scale))
            cloth = cloth.resize(new_size, Image.Resampling.LANCZOS)
            x = (w - cloth.width) // 2
            y = (h - cloth.height) // 2 + 20
            final.paste(cloth, (x, y), cloth)
        self.final_pixmap = self.qpixmap_from_pil(final)
        self.label_result.setPixmap(self.final_pixmap.scaled(
            self.label_result.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
    
    # ---------- 工具函数 ----------
    def pil_from_qpixmap(self, pixmap):
        qimg = pixmap.toImage()
        buf = qimg.bits()
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(qimg.height(), qimg.width(), 4)
        return Image.fromarray(arr, 'RGBA')
    
    def qpixmap_from_pil(self, pil_img):
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)
    
    def on_size_changed(self):
        sender = self.sender()
        try:
            if sender in (self.px_w, self.px_h):
                w = int(self.px_w.text())
                h = int(self.px_h.text())
                dpi = int(self.dpi_edit.text())
                self.mm_w.blockSignals(True)
                self.mm_h.blockSignals(True)
                self.mm_w.setText(f"{w/dpi*25.4:.2f}")
                self.mm_h.setText(f"{h/dpi*25.4:.2f}")
                self.mm_w.blockSignals(False)
                self.mm_h.blockSignals(False)
            elif sender in (self.mm_w, self.mm_h):
                mm_w = float(self.mm_w.text())
                mm_h = float(self.mm_h.text())
                dpi = int(self.dpi_edit.text())
                self.px_w.blockSignals(True)
                self.px_h.blockSignals(True)
                self.px_w.setText(f"{int(mm_w/25.4*dpi)}")
                self.px_h.setText(f"{int(mm_h/25.4*dpi)}")
                self.px_w.blockSignals(False)
                self.px_h.blockSignals(False)
            elif sender == self.dpi_edit:
                dpi = int(self.dpi_edit.text())
                mm_w = float(self.mm_w.text())
                mm_h = float(self.mm_h.text())
                self.px_w.blockSignals(True)
                self.px_h.blockSignals(True)
                self.px_w.setText(f"{int(mm_w/25.4*dpi)}")
                self.px_h.setText(f"{int(mm_h/25.4*dpi)}")
                self.px_w.blockSignals(False)
                self.px_h.blockSignals(False)
        except:
            pass
    
    def load_preset(self, idx):
        if idx <= 0: return
        text = self.spec_combo.currentText()
        parts = text.split(" - ")
        if len(parts) != 2: return
        cat, name = parts[0], parts[1]
        if cat in SPECS_DB and name in SPECS_DB[cat]:
            spec = SPECS_DB[cat][name]
            self.mm_w.setText(str(spec["mm"][0]))
            self.mm_h.setText(str(spec["mm"][1]))
            self.dpi_edit.setText(str(spec["dpi"]))
            self.set_bg_color(QColor(spec["bg"]))
    
    def export_image(self):
        if self.final_pixmap is None:
            QMessageBox.warning(self, "提示", "请先处理照片")
            return
        try:
            w = int(self.px_w.text())
            h = int(self.px_h.text())
        except:
            w, h = 295, 413
        pix = self.final_pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        path, _ = QFileDialog.getSaveFileName(self, "保存图片", f"{self.name_edit.text()}.jpg", "JPEG (*.jpg);;PNG (*.png)")
        if path:
            pix.toImage().save(path, None, self.quality_slider.value())
            QMessageBox.information(self, "完成", f"✅ 导出成功！\n尺寸: {w}×{h}px")
    
    def show_original(self, event):
        if self.original_pixmap:
            self.label_result.setPixmap(self.original_pixmap.scaled(
                self.label_result.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
    
    def show_final(self, event):
        if self.final_pixmap:
            self.label_result.setPixmap(self.final_pixmap.scaled(
                self.label_result.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

# ---------- 启动 ----------
def main():
    app = QApplication(sys.argv)
    win = IDPhotoStudio()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 如果崩溃，显示错误消息框
        import traceback
        error_msg = traceback.format_exc()
        try:
            QMessageBox.critical(None, "程序错误", f"启动失败:\n{error_msg}")
        except:
            print(error_msg)
