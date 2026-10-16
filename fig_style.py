"""
Single style configuration for every MedViHall paper figure.

Change the three venue variables below once the venue is chosen; every figure
reads its size from here.  Nothing in this file is a result: it only fixes
fonts, widths, model order, colours and markers.
"""
import matplotlib as mpl

# ---------------------------------------------------------------- venue sizes
COLUMN_WIDTH_IN = 3.4          # single-column figure width (inches)
DOUBLE_COLUMN_IN = 7.0         # full-width (two-column) figure width (inches)
TEXT_HEIGHT_IN = 9.0           # usable text height of one page (for page budgeting only)

# ---------------------------------------------------------------- typography
FONT_FAMILY = ['DejaVu Sans', 'Arial', 'Helvetica']
FS_BASE = 7.0                  # smallest text anywhere in a figure (>= 7 pt at final size)
FS_LABEL = 7.5
FS_PANEL = 8.5                 # bold panel letters (a), (b), ...
LW_AXIS = 0.6
LW_LINE = 1.0
LW_CI = 1.0
MS = 4.5                       # marker size (pt)
DPI_PNG = 300

# ---------------------------------------------------------------- models
# Presentation order.  Generals first, ascending by core SMHR, then specialists
# (also ascending by core SMHR).  make_figures.py asserts at run time that this
# order equals the SMHR-sorted order computed from the result files.
MODEL_ORDER = ['qwen25vl', 'gemma3', 'internvl3', 'qwen35', 'qwen3vl', 'minicpm',
               'idefics3', 'qwen2vl', 'llava16',
               'huatuogpt', 'chexagent', 'llava_med']
SPECIALISTS = ['huatuogpt', 'chexagent', 'llava_med']          # asserted against is_medical flag
GENERALS = [m for m in MODEL_ORDER if m not in SPECIALISTS]

MODEL_SHORT = {
    'qwen25vl': 'Qwen2.5-VL', 'gemma3': 'Gemma3', 'internvl3': 'InternVL3', 'qwen35': 'Qwen3.5',
    'qwen3vl': 'Qwen3-VL', 'minicpm': 'MiniCPM-V', 'idefics3': 'Idefics3', 'qwen2vl': 'Qwen2-VL',
    'llava16': 'LLaVA-1.6', 'huatuogpt': 'HuatuoGPT-V', 'chexagent': 'CheXagent', 'llava_med': 'LLaVA-Med',
}

# General models: cool hue family (blue -> teal -> green), lightness varies so the
# order survives grayscale; specialists: warm family (orange / vermillion / dark red).
MODEL_COLORS = {
    'qwen25vl': '#08306B', 'gemma3': '#1F5FA8', 'internvl3': '#4A90C8', 'qwen35': '#0B7A75',
    'qwen3vl': '#2FA39A', 'minicpm': '#6C5CB5', 'idefics3': '#3D8B37', 'qwen2vl': '#7FB77E',
    'llava16': '#8FA9BF',
    'huatuogpt': '#E69F00', 'chexagent': '#D55E00', 'llava_med': '#8B1A1A',
}
MODEL_MARKERS = {
    'qwen25vl': 'o', 'gemma3': 's', 'internvl3': '^', 'qwen35': 'v', 'qwen3vl': 'D',
    'minicpm': 'P', 'idefics3': 'X', 'qwen2vl': '<', 'llava16': '>',
    'huatuogpt': '*', 'chexagent': 'h', 'llava_med': 'p',
}
GENERAL_COLOR = '#2171B5'
SPECIALIST_COLOR = '#D55E00'
NEUTRAL = '#595959'
LIGHT_GRAY = '#D9D9D9'

# ---------------------------------------------------------------- modalities / classes
MODALITY_ORDER = ['radiology', 'dermatology', 'histopathology', 'ophthalmology']
MODALITY_SHORT = {'radiology': 'Radiology', 'dermatology': 'Dermatology',
                  'histopathology': 'Histopathology', 'ophthalmology': 'Ophthalmology'}
MODALITY_ABBR = {'radiology': 'Rad', 'dermatology': 'Derm', 'histopathology': 'Histo', 'ophthalmology': 'Ophth'}
NORMAL_STRATA = ('S1', 'DS1', 'HS1', 'OS1')

CLASS_IDS = [1, 2, 3, 4, 5, 6, 7]
CLASS_NAMES = {1: 'Fabrication', 2: 'Omission', 3: 'Misclassification', 4: 'Severity distortion',
               5: 'Anatomical confusion', 6: 'Evasion', 7: 'Clinical-reasoning error'}
# Okabe-Ito based; hatches keep classes separable in grayscale.
CLASS_COLORS = {1: '#D55E00', 2: '#E69F00', 3: '#009E73', 4: '#0072B2', 5: '#CC79A7', 6: '#999999', 7: '#56B4E9'}
CLASS_HATCH = {1: '', 2: '//', 3: '..', 4: '\\\\', 5: 'xx', 6: '', 7: '++'}

STRATEGY_COLORS = {'rag': '#0072B2', 'contrastive': '#CC79A7'}
STRATEGY_MARKERS = {'rag': 'o', 'contrastive': 's'}
STRATEGY_NAMES = {'rag': 'RAG', 'contrastive': 'Contrastive decoding'}


def apply_style():
    mpl.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': FONT_FAMILY,
        'font.size': FS_BASE,
        'axes.labelsize': FS_LABEL,
        'axes.titlesize': FS_LABEL,
        'xtick.labelsize': FS_BASE,
        'ytick.labelsize': FS_BASE,
        'legend.fontsize': FS_BASE,
        'figure.titlesize': FS_LABEL,
        'axes.linewidth': LW_AXIS,
        'xtick.major.width': LW_AXIS,
        'ytick.major.width': LW_AXIS,
        'xtick.major.size': 2.5,
        'ytick.major.size': 2.5,
        'lines.linewidth': LW_LINE,
        'lines.markersize': MS,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': False,
        'grid.color': LIGHT_GRAY,
        'grid.linewidth': 0.4,
        'savefig.dpi': DPI_PNG,
        'figure.dpi': 150,
        'pdf.fonttype': 42,     # embed TrueType so fonts stay editable / >= 7 pt checks pass
        'ps.fonttype': 42,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
        'axes.axisbelow': True,
    })


def panel_label(ax, letter, dx=-0.02, dy=1.02):
    ax.text(dx, dy, f'({letter})', transform=ax.transAxes, fontsize=FS_PANEL, fontweight='bold',
            va='bottom', ha='right' if dx < 0 else 'left')
