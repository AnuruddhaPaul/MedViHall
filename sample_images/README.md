# Sample images

36 example images (12 per modality) from the MedViHall benchmark, for illustration only. File names follow the benchmark image identifiers: `<dataset>_<stratum>_<index>` (see `medvihall_data/data/ground_truth/` for the labels).

| Folder | Source datasets |
|---|---|
| `dermatology/` | ISIC 2020, HAM10000 |
| `histopathology/` | NCT-CRC-HE-100K, PatchCamelyon |
| `ophthalmology/` | REFUGE, ORIGA-light, G1020 |

`contact_sheet.jpg` shows all 36 on one page.

**Licences.** The images belong to the original dataset providers and keep their own licences (several are non-commercial). They are included here only as a small illustration. Check each dataset's licence before reusing them, and obtain the full data from the original sources.

**Known issue.** `ophthalmology/g1020_OS2_0024.jpg` and `ophthalmology/g1020_OS3_0524.jpg` are completely black (maximum pixel value 2 to 3). Other G1020 images in the benchmark should be checked for the same problem.
