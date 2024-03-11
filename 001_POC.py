import lxml.etree as ET
from pathlib import Path
from utils import save, get_present_speakers, xmlid, get_words, teiorg
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s-%(levelname)s - %(message)s"
)


def get_timestamp(e: ET._Element) -> float:
    try:
        return float(exbtimeline[e.get("start")])
    except KeyError:
        logging.error(e.tag, e.attrib, e.text)
        return -1.0


try:
    anno_path = Path(snakemake.input.anno)
    TEI_path = Path(snakemake.input.TEI)
    outpath = Path(snakemake.output[0])
except:
    anno_path = Path(
        "Iriss-disfl-anno-phase2-thomas-exb/2/Iriss-J-Gvecg-P500001.exb.xml"
    )
    TEI_path = Path("iriss_with_w_and_pauses/Iriss-J-Gvecg-P500001.xml")
    outpath = Path("./test.exb.xml")
annodoc = ET.fromstring(anno_path.read_bytes())
TEI = ET.fromstring(TEI_path.read_bytes())
segs_to_assign_synchs = {
    w.getparent()
    for w in TEI.findall(".//{*}w")
    if ("synch" not in w.attrib.keys()) and (w.getparent().tag == teiorg + "seg")
}

for seg in segs_to_assign_synchs:
    for i, w in enumerate(seg.findall(".//{*}w")):
        seg_synch = seg.get("synch")
        if not seg_synch:
            logging.warning(
                "Got a seg that does not have a synch! Will add !! to traceability tier"
            )
            raise Exception(
                f"Seg does not have synch! Seg attrib: {seg.attrib} file {input.TEI}"
            )
        w.set("synch", seg.get("synch", "!!") + f".w{i}")
speakers = get_present_speakers(annodoc)
exbtimeline = {tli.get("id"): tli.get("time") for tli in annodoc.findall(".//tli")}
words = get_words(TEI)
for speaker in speakers:
    new_tier = ET.Element("tier")
    new_tier.set("id", str(len(list(annodoc.findall(".//tier"))) + 1))
    # new_tier.set("speaker", list(speakers)[0])
    new_tier.set("category", "traceability")
    new_tier.set("type", "a")
    new_tier.set("display-name", f"{speaker} [traceability]")
    tier = annodoc.find(f".//tier[@speaker='{speaker}']")
    for event in tier.findall("event"):
        TEI_events = [i for i in words if "#" + event.get("start") == i.get("synch")]
        if len(TEI_events) > 0:
            newevent = ET.Element(
                "event",
                **event.attrib,
            )
            event_start = event.get("start")
            event_end = event.get("end")
            top_tier_event = tier.find(
                f"event[@start='{event_start}'][@end='{event_end}']"
            )
            try:
                first_tier_content = top_tier_event.text.strip()
            except:
                first_tier_content = ""
            if first_tier_content.strip() == TEI_events[0].get("text").strip():
                addendum = ""
            else:
                try:
                    tokenid_to_find = TEI_events[0].get(xmlid + "id")
                    old_traceability_tier = annodoc.find(
                        ".//tier[@display-name='[traceability]']"
                    )

                    possible_events = [
                        e
                        for e in old_traceability_tier.findall(".//{*}event")
                        if e.text.strip().startswith(tokenid_to_find)
                    ]
                    assert len(possible_events) == 1
                    old_event = possible_events[0]
                    newevent.set("start", old_event.get("start"))
                    newevent.set("end", old_event.get("end"))
                    addendum = ""
                    logging.info("Got a !! event, but managed to resolve it.")
                except:
                    addendum = " !! " + TEI_events[0].get("text").strip()
                    logging.warning(
                        "Aww shucks, got a !! event that could not be resolved."
                    )
            newevent.text = TEI_events[0].get(xmlid + "id") + addendum
            new_tier.append(newevent)
    new_tier[:] = sorted(new_tier, key=get_timestamp)
    list(annodoc.findall(".//{*}tier"))[-1].getparent().append(new_tier)
tier_to_delete = annodoc.find(".//tier[@display-name='[traceability]']")
tier_to_delete.getparent().remove(tier_to_delete)
comment = annodoc.find(".//head/meta-information/comment")
from datetime import datetime
comment.text = comment.text + f", traceability tiers added from TEI on {datetime.isoformat(datetime.now())}"
save(annodoc, outpath)
