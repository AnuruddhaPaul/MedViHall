"""
Pillar B (RQ8), Stage 1 -- per-modality reference knowledge bases for RAG.

Built ONLY from reference vocabulary and class definitions: the CheXpert
observation names, HAM10000/ISIC2020 diagnosis categories, NCT-CRC / PatchCamelyon
tissue classes, and glaucoma/CDR clinical thresholds. No per-image labels, no
test images, and no instructions (e.g. "do not guess") are included -- the
snippets are definitions only, so the RAG condition measures added reference
knowledge rather than added prompting. Authored from standard clinical
references; recommend clinician review before publication.
"""

KB = {
    'radiology': [
        ('rad_atelectasis', 'Atelectasis: partial or complete collapse of lung tissue causing volume loss; seen as linear or plate-like opacities, displaced fissures, or an elevated hemidiaphragm.'),
        ('rad_cardiomegaly', 'Cardiomegaly: enlarged cardiac silhouette; on a PA chest radiograph the cardiothoracic ratio exceeds about 0.5.'),
        ('rad_consolidation', 'Consolidation: airspaces filled with fluid, pus, blood or cells, producing a homogeneous opacity that obscures vessels and often shows air bronchograms.'),
        ('rad_edema', 'Pulmonary edema: increased lung fluid; features include vascular redistribution, peribronchial cuffing, Kerley B lines, perihilar bat-wing opacities, and often pleural effusions.'),
        ('rad_enlarged_cm', 'Enlarged cardiomediastinum: widening of the cardiac or mediastinal contour beyond normal limits, caused by vascular, nodal, mass or cardiac disease.'),
        ('rad_fracture', 'Fracture: a break in the continuity of a rib, clavicle, scapula or vertebra, seen as a lucent line or cortical step-off; healing fractures show callus.'),
        ('rad_lung_lesion', 'Lung lesion: a focal pulmonary nodule (under 3 cm) or mass (3 cm or more); benign and malignant causes cannot be reliably separated on a single chest radiograph.'),
        ('rad_lung_opacity', 'Lung opacity: a nonspecific region of increased lung density; the differential includes consolidation, atelectasis, edema and mass.'),
        ('rad_effusion', 'Pleural effusion: fluid in the pleural space causing blunting of the costophrenic angle, a meniscus sign, and a layering opacity on upright films.'),
        ('rad_pleural_other', 'Pleural other: pleural abnormalities other than effusion or pneumothorax, such as pleural thickening, plaques or calcification.'),
        ('rad_pneumonia', 'Pneumonia: infection of the lung parenchyma, typically a focal or multifocal consolidation with air bronchograms; the radiographic appearance does not identify the organism.'),
        ('rad_pneumothorax', 'Pneumothorax: air in the pleural space, seen as a visceral pleural line with absent lung markings beyond it; tension pneumothorax shows mediastinal shift and is an emergency.'),
        ('rad_support_devices', 'Support devices: tubes, lines, pacemakers and other hardware such as endotracheal tubes, central venous catheters and chest drains.'),
        ('rad_no_finding', 'No finding: no acute cardiopulmonary abnormality; clear lungs, normal cardiomediastinal contour and sharp costophrenic angles.'),
    ],
    'dermatology': [
        ('derm_mel', 'Melanoma (mel): malignant melanocytic tumour; dermoscopic features include an atypical pigment network, irregular streaks or pseudopods, blue-white veil, regression structures, and asymmetry of colour and structure.'),
        ('derm_nv', 'Melanocytic nevus (nv): benign melanocytic proliferation with a symmetric pigment network or globular pattern, regular borders and uniform colour.'),
        ('derm_bkl', 'Benign keratosis-like lesion (bkl): includes seborrheic keratosis, solar lentigo and lichen-planus-like keratosis; features include milia-like cysts, comedo-like openings, and fissures and ridges.'),
        ('derm_bcc', 'Basal cell carcinoma (bcc): the most common skin cancer; dermoscopic features include arborizing vessels, blue-gray ovoid nests, leaf-like areas and ulceration, with no pigment network.'),
        ('derm_akiec', 'Actinic keratosis and intraepithelial carcinoma (akiec, including Bowen disease): pre-malignant to in-situ squamous lesions with a scaly, erythematous, keratotic surface and strawberry-pattern vessels.'),
        ('derm_df', 'Dermatofibroma (df): benign fibrous nodule with a central white scar-like patch and a delicate peripheral pigment network.'),
        ('derm_vasc', 'Vascular lesion (vasc): includes angiomas, angiokeratomas and pyogenic granulomas; red, purple or blue lacunae separated by septa, with no pigment network.'),
        ('derm_sk', 'Seborrheic keratosis: benign epidermal tumour with a cerebriform pattern, milia-like cysts and comedo-like openings.'),
        ('derm_lentigo', 'Lentigo NOS and solar lentigo: flat benign pigmented macules of sun-exposed skin with uniform light-brown colour and a sharply demarcated border; lentigo maligna is the malignant counterpart.'),
        ('derm_lichenoid', 'Lichenoid keratosis: a regressing benign lesion, often derived from a solar lentigo or seborrheic keratosis, with granular gray-brown pigmentation on a pink or red background.'),
        ('derm_abcde', 'ABCDE criteria for pigmented lesions: Asymmetry, Border irregularity, Colour variation, Diameter above about 6 mm, and Evolution over time; concern rises with the number of features present.'),
        ('derm_isic', 'ISIC 2020 labels each lesion benign or malignant, with diagnosis categories such as nevus, melanoma, seborrheic keratosis, lentigo NOS, lichenoid keratosis and other.'),
    ],
    'histopathology': [
        ('histo_tum', 'Colorectal adenocarcinoma (TUM): malignant glandular epithelium forming irregular, crowded or cribriform glands with nuclear pleomorphism, hyperchromasia, loss of polarity, mitoses and invasion of surrounding tissue.'),
        ('histo_str', 'Cancer-associated stroma (STR): desmoplastic stroma around a tumour, with fibroblasts and collagen in fibrous bands and myofibroblast activation; few or no malignant cells.'),
        ('histo_deb', 'Debris, mucus and blood (DEB): necrotic cellular debris, mucin pools and extravasated red cells; amorphous material without organised tissue architecture.'),
        ('histo_normal', 'Normal colonic mucosa: regular, evenly spaced crypts lined by columnar cells with goblet cells and basal nuclei, with a thin lamina propria.'),
        ('histo_pcam', 'PatchCamelyon: small H&E patches of breast cancer lymph node sections, labelled tumour present when tumour tissue lies in the central region. Normal lymph node shows small round lymphocytes in follicles and sinuses; metastatic breast carcinoma shows clusters of larger atypical epithelial cells.'),
        ('histo_he', 'H&E staining: nuclei stain blue-purple with haematoxylin, while cytoplasm and extracellular matrix stain pink with eosin.'),
        ('histo_grade', 'Histological grade of colorectal adenocarcinoma is based on gland formation: well differentiated (over 95% glands), moderately differentiated (50-95%), poorly differentiated (under 50%).'),
        ('histo_inflam', 'Inflammatory infiltrate: lymphocytes, plasma cells and neutrophils in the lamina propria or stroma; reactive epithelial atypia can mimic dysplasia.'),
    ],
    'ophthalmology': [
        ('oph_cdr', 'Cup-to-disc ratio (CDR): vertical cup diameter divided by vertical disc diameter. Values below about 0.5 are typical of normal eyes, 0.6 or more is suspicious, and 0.7 or more strongly suggests glaucomatous damage.'),
        ('oph_asym', 'A CDR asymmetry between the two eyes of more than about 0.2 is suspicious for glaucoma.'),
        ('oph_isnt', 'Neuroretinal rim: by the ISNT rule the rim is normally thickest inferiorly, then superiorly, nasally and thinnest temporally; violation of this order or focal rim thinning suggests glaucoma.'),
        ('oph_signs', 'Glaucomatous disc signs include disc haemorrhage, rim notching, bared circumlinear vessels and nasalisation of vessels.'),
        ('oph_rnfl', 'Retinal nerve fibre layer defects appear as wedge-shaped dark areas following arcuate nerve fibre bundles.'),
        ('oph_ppa', 'Peripapillary atrophy of the beta zone is larger and more frequent in glaucoma.'),
        ('oph_discsize', 'Large optic discs have physiologically larger cups, so CDR must be interpreted against disc size; a large CDR on a large disc may be normal.'),
        ('oph_dx', 'Glaucoma is a progressive optic neuropathy diagnosed from optic disc appearance together with intraocular pressure and visual-field loss; a fundus photograph alone supports suspicion rather than a definitive diagnosis.'),
        ('oph_advanced', 'Advanced glaucoma shows a CDR approaching 0.9, near-total rim loss and dense visual-field defects; treatment escalates from medication to laser and surgical options such as trabeculectomy.'),
    ],
}
