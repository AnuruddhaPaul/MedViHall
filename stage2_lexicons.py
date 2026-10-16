"""
Shared keyword lexicons and GT-code mappings for Stage 2 Layer 1 detection
on dermatology, histopathology, and ophthalmology (radiology uses CheXbert
instead -- see stage2_radiology_chexbert.py).

Each modality maps a set of canonical classes to (a) keyword phrases to
match in the VLM's free-text response, and (b) how those canonical classes
relate to the ground-truth fields documented in gt_coverage_notes.json.
"""

# --- Dermatology --------------------------------------------------------
# GT 'diagnosis' field mixes HAM10000 abbreviation codes and ISIC2020 free
# text; both map onto the same canonical classes below.
DERM_DIAGNOSIS_TO_CANONICAL = {
    'mel': 'melanoma', 'melanoma': 'melanoma',
    'nv': 'nevus', 'nevus': 'nevus',
    'bcc': 'basal_cell_carcinoma',
    'akiec': 'actinic_keratosis',
    'bkl': 'benign_keratosis', 'seborrheic keratosis': 'benign_keratosis',
    'lentigo nos': 'benign_keratosis', 'lichenoid keratosis': 'benign_keratosis',
    'df': 'dermatofibroma',
    'vasc': 'vascular_lesion',
}

DERM_KEYWORDS = {
    'melanoma': ['melanoma'],
    'nevus': ['nevus', 'nevi', 'melanocytic nevus', 'mole'],
    'basal_cell_carcinoma': ['basal cell carcinoma', 'bcc'],
    'actinic_keratosis': ['actinic keratosis', 'intraepithelial carcinoma', "bowen's disease", 'bowen disease'],
    'benign_keratosis': ['seborrheic keratosis', 'benign keratosis', 'lentigo', 'lichenoid keratosis'],
    'dermatofibroma': ['dermatofibroma'],
    'vascular_lesion': ['vascular lesion', 'hemangioma', 'angioma'],
    'malignant_generic': ['malignant', 'malignancy', 'cancerous'],
    'benign_generic': ['benign'],
}

# --- Histopathology -------------------------------------------------------
# NCT-CRC subset has a genuine 3-class tissue_class (STR/TUM/DEB); the
# PatchCamelyon subset only has a binary tumor_present flag.
HISTO_TISSUE_TO_CANONICAL = {
    'TUM': 'tumor', 'STR': 'stroma', 'DEB': 'debris',
}

HISTO_KEYWORDS = {
    'tumor': ['tumor', 'tumour', 'adenocarcinoma', 'carcinoma', 'neoplasm', 'malignant', 'cancer', 'malignancy'],
    'stroma': ['stroma', 'stromal'],
    'debris': ['debris', 'necrotic debris', 'necrosis', 'mucus'],
    'benign_generic': ['benign', 'no tumor', 'no malignancy'],
}

# --- Ophthalmology --------------------------------------------------------
OPHTH_KEYWORDS = {
    'glaucoma': ['glaucoma', 'glaucomatous'],
    'normal_disc': ['normal optic disc', 'no glaucoma', 'healthy optic nerve'],
    'cdr_elevated': ['elevated cup-to-disc ratio', 'increased cup-to-disc ratio', 'high cup-to-disc ratio',
                      'elevated cdr', 'increased cdr', 'high cdr', 'suspicious cup-to-disc ratio'],
}
