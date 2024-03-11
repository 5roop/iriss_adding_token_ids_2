import lxml.etree as ET
from pathlib import Path


xmlid = "{http://www.w3.org/XML/1998/namespace}"


def save(exb: ET._Document, outpath: Path) -> None:
    ET.indent(exb, space="\t")
    exb.getroottree().write(
        outpath,
        pretty_print=True,
        encoding="utf8",
        xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
    )
    outpath.write_text(
        outpath.read_text().replace(
            "<?xml version='1.0' encoding='UTF8'?>",
            '<?xml version="1.0" encoding="UTF-8"?>',
        )
    )


def get_present_speakers(exb: ET._Document) -> set[str]:
    tiers = exb.findall(".//tier")
    return set([i.get("speaker") for i in tiers if i.get("speaker") is not None])


def get_words(tei: ET._Element) -> list[dict]:  # type: ignore
    timeline = get_timeline(tei)
    all_elements_with_synch = tei.findall(".//{*}*[@synch]")
    all_synchs = [i.get("synch").replace("#", "") for i in all_elements_with_synch]

    def find_next(synch: str) -> str | None:
        if synch == None:
            return None
        synch = synch.replace("#", "")
        if synch == all_synchs[-1]:
            return synch
        for i, s in enumerate(all_synchs):
            if s == synch:
                return all_synchs[i + 1]
        else:
            raise ValueError(
                f"Iterated though all synchs, couldn't find a match for {synch}."
            )

    all_words = tei.findall(".//{*}w")
    return [
        {**w.attrib, "next_synch": find_next(w.get("synch")), "text": w.text}
        for w in all_words
    ]


def get_timeline(tei: ET._Element) -> dict:
    whens = tei.findall(".//{*}when")
    return {when.get(xmlid + "id"): when.get("interval") for when in whens}


teiorg = "{http://www.tei-c.org/ns/1.0}"
