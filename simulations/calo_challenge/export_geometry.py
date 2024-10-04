from Configurables import GaussinoGeometry

GaussinoGeometry().ExportGDML = {
    "GDMLFileName": "calochallenge.gdml",
    # G4 will crash if the file with same name already exists
    "GDMLFileNameOverwrite": True,
    # add unique references to the names
    "GDMLAddReferences": True,
    # export auxilliary information
    "GDMLExportEnergyCuts": True,
    "GDMLExportSD": True,
}
