from pathlib import Path

all_inputs = Path("Iriss-disfl-anno-phase2-thomas-exb/2/").glob("*.xml")

rule All:
    input: [Path("Iriss-disfl-anno-phase3-new_tokens")/i.name for i in all_inputs]


rule Single:
    input:
        anno="Iriss-disfl-anno-phase2-thomas-exb/2/{file}.exb.xml",
        TEI="iriss_with_w_and_pauses/{file}.xml"
    output:
        "Iriss-disfl-anno-phase3-new_tokens/{file}.exb.xml"
    script:
        "001_POC.py"
